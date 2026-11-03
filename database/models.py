"""Modelos do FIDES, traduzidos do Diagrama de Classes (versão de 30/10/2026).

Classes da UML: Santo, Oracao, Novena, DiaNovena, Livro, Agenda, LiturgiaDia e
LiturgiaHora. Elementos que existem só no banco (não são classes da UML):
  * ``MomentoDia`` + ``Oracao_Momento_Dia``: forma de persistir o enum
    ``MomentoDoDia`` da UML (lista de momentos de cada oração);
  * ``Oracao_Dia_Novena``: tabela associativa DiaNovena -> Oração (N:N);
  * ``Administrador``: autenticação do ator Administrador (RNF05).

Convenções:
  * tabelas com inicial maiúscula (Santos, Oracoes, Dias_Novena...);
  * colunas no formato ``campo_entidade`` e chaves ``id_entidade`` (a FK tem o
    mesmo nome da PK que referencia);
  * enums gravados como VARCHAR com o NOME do membro (ex.: ``AO_ACORDAR``); o
    rótulo para exibição é o ``.value`` (ex.: "Ao acordar").

Os atributos Python seguem os nomes do diagrama (``santo.nome``,
``livro.livro_recomendado``...), enquanto o nome físico da coluna segue a
convenção acima (``Column("nome_santo", ...)``).

Transações: os métodos de escrita (``cadastrar``, ``atualizar``, ``excluir``,
``categorizar`` e os da Agenda) fazem ``flush`` e NÃO dão ``commit``. Quem chama
(rota da API ou seeds) decide quando confirmar ou desfazer a transação. Depois de
qualquer exceção lançada por um método de escrita, faça ``session.rollback()``.

Escopo: os métodos de escrita existem no modelo e exigem token de administrador
(RNF05), mas a interface administrativa (rotas de escrita) é da Fase 2. No MVP o
conteúdo entra pelos seeds (RNF09).
"""
import base64
import enum
import hashlib
import hmac
import json
import os
import secrets
import time
import unicodedata
from datetime import date, datetime, timedelta

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    select,
    text,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import object_session, relationship, validates

from .connection import Base

# --------------------------------------------------------------------------- #
# Constantes de negócio (RNFs)
# --------------------------------------------------------------------------- #
LIMITE_MAXIMO_POR_PAGINA = 20  # RNF02 - paginação de no máximo 20 itens
INTERVALO_LITURGIA_DIAS = 7  # RNF07 - 1 semana para trás e para frente
DIAS_DA_NOVENA = 9
TOKEN_VALIDADE_SEGUNDOS = 3600
SECRET_KEY = os.getenv("FIDES_SECRET_KEY", "dev-only-troque-em-producao")


# --------------------------------------------------------------------------- #
# Exceções de domínio
# --------------------------------------------------------------------------- #
class AutenticacaoError(Exception):
    """Credenciais inválidas ou token ausente/expirado/adulterado (RNF05)."""


class DadosInvalidosError(ValueError):
    """Dados de cadastro/atualização incompletos ou inconsistentes."""


class RegistroDuplicadoError(DadosInvalidosError):
    """Operação que viola uma regra de unicidade.

    Após este erro a transação da sessão deve ser desfeita (``rollback``).
    """


class RegistroNaoEncontradoError(DadosInvalidosError):
    """O registro informado (por id) não existe."""


class ForaDoIntervaloError(ValueError):
    """Data fora da janela de ±1 semana da liturgia (RNF07)."""

    def __init__(self):
        super().__init__(
            "Esta data está fora do intervalo disponível na versão de "
            "demonstração (1 semana antes e 1 semana depois de hoje)."
        )


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class BlocoMomento(enum.Enum):
    """Enum ``MomentoDoDia`` da UML (inalterado em relação à versão anterior)."""

    AO_ACORDAR = "Ao acordar"
    REFEICOES = "Refeições"
    MISSA = "Missa"
    ANTES_DE_DORMIR = "Antes de dormir"


class BlocoLiturgia(enum.Enum):
    """Enum ``LiturgiaHora.bloco`` da UML (Laudes, HorasMedias, Vesperas)."""

    LAUDES = "Laudes"
    HORAS_MEDIAS = "Horas médias"
    VESPERAS = "Vésperas"


class TipoAgenda(enum.Enum):
    """Enum ``Agenda.tipo`` da UML."""

    NOVENA = "Novena"
    LITURGIA = "Liturgia"


class StatusAgenda(enum.Enum):
    """Enum ``Agenda.status`` da UML."""

    ATIVA = "Ativa"
    CANCELADA = "Cancelada"
    CONCLUIDA = "Concluída"


# --------------------------------------------------------------------------- #
# Helpers internos
# --------------------------------------------------------------------------- #
def _normalizar(texto: str) -> str:
    """Minúsculas e sem acentos, para buscas ('Tomas' encontra 'Tomás')."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower().strip()


def _paginar(consulta, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
    pagina = max(int(pagina), 1)
    limite = min(max(int(limite), 1), LIMITE_MAXIMO_POR_PAGINA)
    return consulta.limit(limite).offset((pagina - 1) * limite)


def _exigir_campos(dados: dict, *campos: str) -> None:
    faltando = [c for c in campos if not dados.get(c)]
    if faltando:
        raise DadosInvalidosError(f"Campos obrigatórios ausentes: {', '.join(faltando)}")


def _validar_alteracoes(dados, editaveis, obrigatorios=()) -> None:
    """Regras comuns aos métodos ``atualizar`` (atualização parcial).

    Só os campos presentes em ``dados`` são alterados. Campos fora de
    ``editaveis`` são rejeitados, e campos obrigatórios não podem ficar vazios.
    """
    if not isinstance(dados, dict) or not dados:
        raise DadosInvalidosError("Informe ao menos um campo para atualizar.")
    desconhecidos = sorted(set(dados) - set(editaveis))
    if desconhecidos:
        raise DadosInvalidosError(f"Campos não editáveis ou desconhecidos: {', '.join(desconhecidos)}")
    vazios = [c for c in obrigatorios if c in dados and not dados[c]]
    if vazios:
        raise DadosInvalidosError(f"Campos obrigatórios não podem ficar vazios: {', '.join(vazios)}")


def _persistir(session, objeto, descricao: str) -> None:
    """``add`` + ``flush`` traduzindo violações de unicidade em erro de domínio."""
    session.add(objeto)
    try:
        session.flush()
    except IntegrityError as erro:
        mensagem = str(erro.orig).upper()
        if "UNIQUE" in mensagem or "DUPLICATE" in mensagem:
            raise RegistroDuplicadoError(f"Já existe {descricao}.") from erro
        raise


def _remover(session, objeto, descricao: str) -> None:
    """``delete`` + ``flush`` traduzindo violações de integridade."""
    session.delete(objeto)
    try:
        session.flush()
    except IntegrityError as erro:
        mensagem = str(erro.orig).upper()
        if "UNIQUE" in mensagem or "DUPLICATE" in mensagem:
            raise RegistroDuplicadoError(
                f"Não foi possível excluir {descricao}: um conteúdo vinculado ficaria "
                "com título repetido ao perder o vínculo.") from erro
        if "FOREIGN KEY" in mensagem:
            raise DadosInvalidosError(
                f"Não foi possível excluir {descricao}: há registros vinculados.") from erro
        raise


def _sessao_de(objeto):
    session = object_session(objeto)
    if session is None:
        raise DadosInvalidosError("O registro precisa estar associado a uma sessão do banco.")
    return session


def _buscar_ou_erro(session, modelo, id_registro, nome: str):
    registro = session.get(modelo, id_registro) if id_registro is not None else None
    if registro is None:
        raise RegistroNaoEncontradoError(f"{nome} {id_registro} não encontrado(a).")
    return registro


def _validar_santo(session, santo_id) -> None:
    if santo_id is not None and session.get(Santo, santo_id) is None:
        raise DadosInvalidosError(f"Santo {santo_id} não encontrado.")


def _converter_data(valor, campo: str = "data") -> date:
    """Aceita ``date`` (ou ``datetime``) e texto ISO ``AAAA-MM-DD``."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor)
        except ValueError:
            pass
    raise DadosInvalidosError(f"O campo '{campo}' deve ser uma data (AAAA-MM-DD).")


def _converter_enum(tipo_enum, valor, campo: str):
    """Aceita o membro do enum ou seu nome em texto (ex.: 'laudes')."""
    if isinstance(valor, tipo_enum):
        return valor
    if isinstance(valor, str):
        try:
            return tipo_enum[valor.strip().upper()]
        except KeyError:
            pass
    opcoes = ", ".join(m.name for m in tipo_enum)
    raise DadosInvalidosError(f"Valor inválido para '{campo}'. Opções: {opcoes}.")


def _buscar_oracoes(session, ids) -> list:
    """Orações pelos ids, rejeitando ids inexistentes."""
    ids = list(dict.fromkeys(ids or []))
    if not ids:
        return []
    with session.no_autoflush:
        encontradas = list(session.scalars(select(Oracao).where(Oracao.id.in_(ids))))
    faltando = sorted(set(ids) - {o.id for o in encontradas})
    if faltando:
        raise DadosInvalidosError(f"Orações não encontradas: {faltando}")
    por_id = {o.id: o for o in encontradas}
    return [por_id[i] for i in ids]


def _resolver_momentos(session, itens) -> list:
    """Converte ids, nomes, ``BlocoMomento`` ou ``MomentoDia`` em ``MomentoDia``."""
    resultado = []
    with session.no_autoflush:
        for item in itens or []:
            if isinstance(item, MomentoDia):
                momento = item
            elif isinstance(item, (BlocoMomento, str)):
                bloco = _converter_enum(BlocoMomento, item, "momento")
                momento = session.scalar(select(MomentoDia).where(MomentoDia.bloco == bloco))
            elif isinstance(item, int) and not isinstance(item, bool):
                momento = session.get(MomentoDia, item)
            else:
                momento = None
            if momento is None:
                raise DadosInvalidosError(f"Momento do dia inválido ou não cadastrado: {item!r}")
            if momento not in resultado:
                resultado.append(momento)
    return resultado


def _exigir_autenticacao(token) -> None:
    """Bloqueia operações administrativas sem token válido (RNF05)."""
    if not Administrador._validar_token(token):
        raise AutenticacaoError("Token inválido ou expirado.")


def _hash_senha(senha: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    iteracoes = 200_000
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), iteracoes)
    return f"pbkdf2_sha256${iteracoes}${salt}${digest.hex()}"


def _verificar_senha(senha: str, armazenado: str) -> bool:
    try:
        _, iteracoes, salt, esperado = armazenado.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), int(iteracoes))
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(digest.hex(), esperado)


# --------------------------------------------------------------------------- #
# Tabelas associativas (N..N)
# --------------------------------------------------------------------------- #
Oracao_Momento_Dia = Table(
    "Oracao_Momento_Dia",
    Base.metadata,
    Column("id_oracao", Integer, ForeignKey("Oracoes.id_oracao", ondelete="CASCADE"),
           primary_key=True),
    Column("id_momento_dia", Integer, ForeignKey("Momentos_Dia.id_momento_dia", ondelete="CASCADE"),
           primary_key=True),
)

Oracao_Dia_Novena = Table(
    "Oracao_Dia_Novena",
    Base.metadata,
    Column("id_dia_novena", Integer, ForeignKey("Dias_Novena.id_dia_novena", ondelete="CASCADE"),
           primary_key=True),
    Column("id_oracao", Integer, ForeignKey("Oracoes.id_oracao", ondelete="CASCADE"),
           primary_key=True),
)


# --------------------------------------------------------------------------- #
# Administrador (existe no banco; não é classe da UML - ator Administrador)
# --------------------------------------------------------------------------- #
class Administrador(Base):
    __tablename__ = "Administradores"

    id = Column("id_administrador", Integer, primary_key=True)
    nome = Column("nome_administrador", String, nullable=False)
    # Identificador de autenticação do MVP (ex.: "adm"). Único.
    login = Column("login_administrador", String, nullable=False, unique=True)
    # E-mail é opcional; quando preenchido, também pode ser usado para entrar.
    email = Column("email_administrador", String, unique=True)
    senha_hash = Column("senha_hash_administrador", String, nullable=False)

    def definir_senha(self, senha: str) -> None:
        self.senha_hash = _hash_senha(senha)

    def emitir_token(self) -> str:
        """Emite um token assinado (HMAC-SHA256) para este administrador.

        Não verifica senha: use ``autenticar`` para fluxos de login. Existe
        para processos internos confiáveis (ex.: seeds) que precisam chamar os
        métodos protegidos sem contornar a validação do token.
        """
        payload = {"sub": self.id, "exp": int(time.time()) + TOKEN_VALIDADE_SEGUNDOS}
        corpo = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        assinatura = hmac.new(SECRET_KEY.encode(), corpo.encode(), hashlib.sha256).hexdigest()
        return f"{corpo}.{assinatura}"

    @classmethod
    def autenticar(cls, session, login: str, senha: str) -> str:
        """Valida credenciais e devolve um token assinado.

        ``login`` é o identificador principal; por compatibilidade, se nenhum
        administrador tiver esse login, tenta casar com o e-mail.
        """
        admin = None
        if login:
            login = login.strip()
            admin = session.scalar(select(cls).where(cls.login == login))
            if admin is None:
                admin = session.scalar(select(cls).where(cls.email == login))
        # verifica mesmo sem usuário, para não vazar por tempo de resposta
        hash_alvo = admin.senha_hash if admin else _hash_senha("senha-inexistente")
        if not _verificar_senha(senha or "", hash_alvo) or admin is None:
            raise AutenticacaoError("Login ou senha inválidos.")
        return admin.emitir_token()

    @staticmethod
    def _validar_token(token) -> bool:  # protegido
        try:
            corpo, assinatura = token.split(".")
            esperada = hmac.new(SECRET_KEY.encode(), corpo.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(assinatura, esperada):
                return False
            payload = json.loads(base64.urlsafe_b64decode(corpo.encode()))
            return payload["exp"] > time.time()
        except (ValueError, KeyError, AttributeError, TypeError):
            return False


# --------------------------------------------------------------------------- #
# Santo
# --------------------------------------------------------------------------- #
class Santo(Base):
    __tablename__ = "Santos"

    id = Column("id_santo", Integer, primary_key=True)
    nome = Column("nome_santo", String, nullable=False, unique=True)
    # Nome sem acento/minúsculo, usado por buscar_nome(). Preenchido automaticamente.
    nome_busca = Column("nome_busca_santo", String, index=True)
    foto_url = Column("foto_url_santo", String)
    biografia = Column("biografia_santo", Text)

    # Associações simples e opcionais (UML 0..1 — 0..*), não composições: ao
    # excluir um santo, os conteúdos permanecem e perdem o vínculo (SET NULL).
    oracoes = relationship("Oracao", back_populates="santo", passive_deletes=True,
                           order_by="Oracao.titulo")
    novenas = relationship("Novena", back_populates="santo", passive_deletes=True,
                           order_by="Novena.titulo")
    livros = relationship("Livro", back_populates="santo", passive_deletes=True,
                          order_by="Livro.titulo")

    @validates("nome")
    def _atualizar_nome_busca(self, _chave, valor):
        self.nome_busca = _normalizar(valor) if valor else None
        return valor

    # -- leitura (rotas públicas, RNF06) --
    @classmethod
    def listar_todos(cls, session, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
        return list(session.scalars(_paginar(select(cls).order_by(cls.nome), pagina, limite)))

    @classmethod
    def buscar_nome(cls, session, nome: str):
        termo = f"%{_normalizar(nome)}%"
        return list(session.scalars(select(cls).where(cls.nome_busca.like(termo)).order_by(cls.nome)))

    @classmethod
    def buscar_id(cls, session, id_santo: int):
        return session.get(cls, id_santo)

    def ver_oracao_santo(self):
        return list(self.oracoes)

    def ver_novena_santo(self):
        return list(self.novenas)

    def ver_livro_santo(self):
        return list(self.livros)

    # -- escrita (protegida, RNF05; interface na Fase 2) --
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "nome")
        santo = cls(nome=dados["nome"], foto_url=dados.get("foto_url"),
                    biografia=dados.get("biografia"))
        _persistir(session, santo, f"um santo chamado '{dados['nome']}'")
        return santo

    @classmethod
    def atualizar(cls, session, id_santo: int, dados: dict, token: str):
        """Atualiza nome, foto_url e/ou biografia (só os campos informados)."""
        _exigir_autenticacao(token)
        _validar_alteracoes(dados, {"nome", "foto_url", "biografia"}, obrigatorios=("nome",))
        santo = _buscar_ou_erro(session, cls, id_santo, "Santo")
        for campo, valor in dados.items():
            setattr(santo, campo, valor)
        _persistir(session, santo, f"um santo chamado '{santo.nome}'")
        return santo

    @classmethod
    def excluir(cls, session, id_santo: int, token: str) -> None:
        """Exclui o santo. Orações, novenas e livros dele ficam sem santo (SET NULL)."""
        _exigir_autenticacao(token)
        santo = _buscar_ou_erro(session, cls, id_santo, "Santo")
        _remover(session, santo, f"o santo '{santo.nome}'")


# --------------------------------------------------------------------------- #
# Momento do dia (persistência do enum MomentoDoDia)
# --------------------------------------------------------------------------- #
class MomentoDia(Base):
    __tablename__ = "Momentos_Dia"

    id = Column("id_momento_dia", Integer, primary_key=True)
    bloco = Column("bloco_momento_dia", Enum(BlocoMomento), nullable=False, unique=True)

    oracoes = relationship("Oracao", secondary=Oracao_Momento_Dia, back_populates="momentos",
                           passive_deletes=True)

    @classmethod
    def listar_todos(cls, session):
        return list(session.scalars(select(cls).order_by(cls.id)))


# --------------------------------------------------------------------------- #
# Oração
# --------------------------------------------------------------------------- #
class Oracao(Base):
    __tablename__ = "Oracoes"
    __table_args__ = (
        # Unicidade de título: oração geral (sem santo) e oração de santo são
        # regras separadas, pois NULL não conta como igual em UNIQUE comum.
        Index("uq_oracao_titulo_geral", "titulo_oracao", unique=True,
              sqlite_where=text("id_santo IS NULL"),
              postgresql_where=text("id_santo IS NULL")),
        Index("uq_oracao_titulo_por_santo", "id_santo", "titulo_oracao", unique=True,
              sqlite_where=text("id_santo IS NOT NULL"),
              postgresql_where=text("id_santo IS NOT NULL")),
    )

    id = Column("id_oracao", Integer, primary_key=True)
    titulo = Column("titulo_oracao", String, nullable=False)
    texto = Column("texto_oracao", Text, nullable=False)
    basica = Column("basica_oracao", Boolean, nullable=False, default=False)
    # Nulo para orações gerais (ex.: Pai Nosso), que não pertencem a um santo.
    santo_id = Column("id_santo", Integer, ForeignKey("Santos.id_santo", ondelete="SET NULL"))

    santo = relationship("Santo", back_populates="oracoes")
    # Atributo ``momentos: List<MomentoDoDia>`` da UML.
    momentos = relationship("MomentoDia", secondary=Oracao_Momento_Dia, back_populates="oracoes",
                            passive_deletes=True)
    dias_novena = relationship("DiaNovena", secondary=Oracao_Dia_Novena, back_populates="oracoes",
                               passive_deletes=True)

    # -- leitura --
    @classmethod
    def listar_todas(cls, session, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
        return list(session.scalars(_paginar(select(cls).order_by(cls.titulo), pagina, limite)))

    @classmethod
    def listar_basicas(cls, session, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
        consulta = select(cls).where(cls.basica.is_(True)).order_by(cls.id)
        return list(session.scalars(_paginar(consulta, pagina, limite)))

    @classmethod
    def filtrar_momento(cls, session, momento, pagina: int = 1,
                        limite: int = LIMITE_MAXIMO_POR_PAGINA):
        """Orações de um momento do dia.

        ``momento`` pode ser o enum ``BlocoMomento`` (como na UML), o nome em texto
        (ex.: 'ao_acordar'), um ``MomentoDia`` ou o id do momento (usado pela API).
        """
        consulta = select(cls).join(cls.momentos)
        if isinstance(momento, MomentoDia):
            consulta = consulta.where(MomentoDia.id == momento.id)
        elif isinstance(momento, (BlocoMomento, str)):
            consulta = consulta.where(MomentoDia.bloco == _converter_enum(BlocoMomento, momento, "momento"))
        else:
            consulta = consulta.where(MomentoDia.id == momento)
        return list(session.scalars(_paginar(consulta.order_by(cls.titulo), pagina, limite)))

    @classmethod
    def buscar_por_santo(cls, session, santo_id: int):
        return list(session.scalars(select(cls).where(cls.santo_id == santo_id).order_by(cls.titulo)))

    # -- escrita --
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "titulo", "texto")
        santo_id = dados.get("santo_id")
        _validar_santo(session, santo_id)
        oracao = cls(titulo=dados["titulo"], texto=dados["texto"],
                     basica=bool(dados.get("basica", False)), santo_id=santo_id)
        if dados.get("momentos_ids"):
            oracao.categorizar(_resolver_momentos(session, dados["momentos_ids"]), token)
        escopo = "para este santo" if santo_id is not None else "entre as orações gerais"
        _persistir(session, oracao, f"uma oração '{dados['titulo']}' {escopo}")
        return oracao

    @classmethod
    def atualizar(cls, session, id_oracao: int, dados: dict, token: str):
        """Atualiza titulo, texto, basica, santo_id e/ou momentos_ids."""
        _exigir_autenticacao(token)
        _validar_alteracoes(dados, {"titulo", "texto", "basica", "santo_id", "momentos_ids"},
                            obrigatorios=("titulo", "texto"))
        oracao = _buscar_ou_erro(session, cls, id_oracao, "Oração")
        if "santo_id" in dados:
            _validar_santo(session, dados["santo_id"])
        with session.no_autoflush:
            for campo in ("titulo", "texto", "santo_id"):
                if campo in dados:
                    setattr(oracao, campo, dados[campo])
            if "basica" in dados:
                oracao.basica = bool(dados["basica"])
            if "momentos_ids" in dados:
                oracao.categorizar(_resolver_momentos(session, dados["momentos_ids"]), token)
        escopo = "para este santo" if oracao.santo_id is not None else "entre as orações gerais"
        _persistir(session, oracao, f"uma oração '{oracao.titulo}' {escopo}")
        return oracao

    @classmethod
    def excluir(cls, session, id_oracao: int, token: str) -> None:
        """Exclui a oração; ela sai dos momentos do dia e dos dias de novena."""
        _exigir_autenticacao(token)
        oracao = _buscar_ou_erro(session, cls, id_oracao, "Oração")
        _remover(session, oracao, f"a oração '{oracao.titulo}'")

    def categorizar(self, momentos, token: str) -> None:
        """Define (substitui) os momentos do dia em que a oração é indicada (US20).

        Aceita ``MomentoDia`` ou, se a oração já estiver em uma sessão, também
        ``BlocoMomento``, nomes em texto ou ids.
        """
        _exigir_autenticacao(token)
        itens = list(momentos or [])
        if all(isinstance(m, MomentoDia) for m in itens):
            self.momentos = itens
        else:
            self.momentos = _resolver_momentos(_sessao_de(self), itens)


# --------------------------------------------------------------------------- #
# Novena e DiaNovena (composição 1 — 9)
# --------------------------------------------------------------------------- #
class Novena(Base):
    __tablename__ = "Novenas"
    __table_args__ = (
        # Santo é opcional (UML 0..1): título único entre as novenas sem santo e
        # par (santo, título) único entre as novenas de um santo.
        Index("uq_novena_titulo_geral", "titulo_novena", unique=True,
              sqlite_where=text("id_santo IS NULL"),
              postgresql_where=text("id_santo IS NULL")),
        Index("uq_novena_titulo_por_santo", "id_santo", "titulo_novena", unique=True,
              sqlite_where=text("id_santo IS NOT NULL"),
              postgresql_where=text("id_santo IS NOT NULL")),
    )

    id = Column("id_novena", Integer, primary_key=True)
    titulo = Column("titulo_novena", String, nullable=False)
    descricao = Column("descricao_novena", Text)
    santo_id = Column("id_santo", Integer, ForeignKey("Santos.id_santo", ondelete="SET NULL"))

    santo = relationship("Santo", back_populates="novenas")
    dias = relationship("DiaNovena", back_populates="novena", cascade="all, delete-orphan",
                        passive_deletes=True, order_by="DiaNovena.numero_dia")
    agendas = relationship("Agenda", back_populates="novena", passive_deletes=True,
                           order_by="Agenda.data_inicio")

    @classmethod
    def listar_todas(cls, session, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
        return list(session.scalars(_paginar(select(cls).order_by(cls.titulo), pagina, limite)))

    @classmethod
    def buscar_id(cls, session, id_novena: int):
        return session.get(cls, id_novena)

    @classmethod
    def buscar_santo(cls, session, santo_id: int):
        return list(session.scalars(select(cls).where(cls.santo_id == santo_id).order_by(cls.titulo)))

    def obter_dias(self):
        return list(self.dias)

    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        """Cadastra a novena com seus 9 dias (US21).

        ``dados["dias"]`` deve conter exatamente 9 itens, cada um no formato
        ``{"texto_reflexao": str, "oracoes_base_ids": [int, ...]}``.
        ``dados["santo_id"]`` é opcional (UML 0..1).
        """
        _exigir_autenticacao(token)
        _exigir_campos(dados, "titulo")
        dias = dados.get("dias") or []
        if len(dias) != DIAS_DA_NOVENA:
            raise DadosInvalidosError(f"Uma novena precisa ter exatamente {DIAS_DA_NOVENA} dias.")
        santo_id = dados.get("santo_id")
        _validar_santo(session, santo_id)

        novena = cls(titulo=dados["titulo"], descricao=dados.get("descricao"), santo_id=santo_id)
        with session.no_autoflush:  # a novena ainda está sendo montada fora da sessão
            for numero, dia in enumerate(dias, start=1):
                _exigir_campos(dia, "texto_reflexao")
                item = DiaNovena(numero_dia=numero, texto_reflexao=dia["texto_reflexao"])
                item.oracoes = _buscar_oracoes(session, dia.get("oracoes_base_ids"))
                novena.dias.append(item)
        escopo = "para este santo" if santo_id is not None else "sem santo associado"
        _persistir(session, novena, f"uma novena '{dados['titulo']}' {escopo}")
        return novena

    @classmethod
    def atualizar(cls, session, id_novena: int, dados: dict, token: str):
        """Atualiza titulo, descricao e/ou santo_id. Os dias mudam por DiaNovena.atualizar."""
        _exigir_autenticacao(token)
        _validar_alteracoes(dados, {"titulo", "descricao", "santo_id"}, obrigatorios=("titulo",))
        novena = _buscar_ou_erro(session, cls, id_novena, "Novena")
        if "santo_id" in dados:
            _validar_santo(session, dados["santo_id"])
        for campo, valor in dados.items():
            setattr(novena, campo, valor)
        escopo = "para este santo" if novena.santo_id is not None else "sem santo associado"
        _persistir(session, novena, f"uma novena '{novena.titulo}' {escopo}")
        return novena

    @classmethod
    def excluir(cls, session, id_novena: int, token: str) -> None:
        """Exclui a novena e seus 9 dias (composição).

        Não exclui se houver agenda em andamento ou futura: cancele-a antes
        (``Agenda.cancelar``). Agendas encerradas ficam como histórico, sem novena.
        """
        _exigir_autenticacao(token)
        novena = _buscar_ou_erro(session, cls, id_novena, "Novena")
        if Agenda.buscar_ativa(session, novena.id) is not None:
            raise DadosInvalidosError(
                "Esta novena tem uma agenda ativa. Cancele a agenda antes de excluir a novena.")
        _remover(session, novena, f"a novena '{novena.titulo}'")


class DiaNovena(Base):
    __tablename__ = "Dias_Novena"
    __table_args__ = (
        UniqueConstraint("id_novena", "numero_dia_novena", name="uq_dia_novena_numero"),
        CheckConstraint("numero_dia_novena BETWEEN 1 AND 9", name="ck_dia_novena_intervalo"),
    )

    id = Column("id_dia_novena", Integer, primary_key=True)
    novena_id = Column("id_novena", Integer, ForeignKey("Novenas.id_novena", ondelete="CASCADE"),
                       nullable=False)
    numero_dia = Column("numero_dia_novena", Integer, nullable=False)
    texto_reflexao = Column("texto_reflexao_dia_novena", Text, nullable=False)

    novena = relationship("Novena", back_populates="dias")
    # Orações base do dia (Pai Nosso, Ave Maria...) - N..N com Oração.
    oracoes = relationship("Oracao", secondary=Oracao_Dia_Novena, back_populates="dias_novena",
                           passive_deletes=True)

    @classmethod
    def buscar_novena_dia(cls, session, novena_id: int, dia: int):
        return session.scalar(
            select(cls).where(cls.novena_id == novena_id, cls.numero_dia == dia))

    @classmethod
    def listar_novena(cls, session, novena_id: int):
        return list(session.scalars(
            select(cls).where(cls.novena_id == novena_id).order_by(cls.numero_dia)))

    def obter_oracao_base(self):
        return list(self.oracoes)

    @classmethod
    def atualizar(cls, session, id_dia_novena: int, dados: dict, token: str):
        """Atualiza texto_reflexao e/ou oracoes_base_ids de um dia.

        ``numero_dia`` e ``novena_id`` não mudam: a composição Novena 1 — 9 é
        mantida. Pelo mesmo motivo não existem ``cadastrar``/``excluir`` de um dia
        isolado: os dias nascem e morrem com a novena.
        """
        _exigir_autenticacao(token)
        _validar_alteracoes(dados, {"texto_reflexao", "oracoes_base_ids"},
                            obrigatorios=("texto_reflexao",))
        dia = _buscar_ou_erro(session, cls, id_dia_novena, "Dia de novena")
        if "texto_reflexao" in dados:
            dia.texto_reflexao = dados["texto_reflexao"]
        if "oracoes_base_ids" in dados:
            dia.oracoes = _buscar_oracoes(session, dados["oracoes_base_ids"])
        _persistir(session, dia, f"o dia {dia.numero_dia} nesta novena")
        return dia


# --------------------------------------------------------------------------- #
# Livro
# --------------------------------------------------------------------------- #
class Livro(Base):
    __tablename__ = "Livros"
    __table_args__ = (UniqueConstraint("titulo_livro", "autor_livro", name="uq_livro_titulo_autor"),)

    id = Column("id_livro", Integer, primary_key=True)
    titulo = Column("titulo_livro", String, nullable=False)
    autor = Column("autor_livro", String, nullable=False)
    resumo = Column("resumo_livro", Text)
    contexto_historico = Column("contexto_historico_livro", Text)
    # UC13 / US12: obras indicadas para começar os estudos ("por onde começar").
    livro_recomendado = Column("recomendado_livro", Boolean, nullable=False, default=False)
    # Nulo para obras que não estão ligadas a um santo (ex.: Scott Hahn).
    santo_id = Column("id_santo", Integer, ForeignKey("Santos.id_santo", ondelete="SET NULL"))

    santo = relationship("Santo", back_populates="livros")

    @classmethod
    def listar_todos(cls, session, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
        return list(session.scalars(_paginar(select(cls).order_by(cls.titulo), pagina, limite)))

    @classmethod
    def listar_recomendados(cls, session, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
        consulta = select(cls).where(cls.livro_recomendado.is_(True)).order_by(cls.titulo)
        return list(session.scalars(_paginar(consulta, pagina, limite)))

    @classmethod
    def buscar_id(cls, session, id_livro: int):
        return session.get(cls, id_livro)

    @classmethod
    def buscar_santo(cls, session, santo_id: int):
        return list(session.scalars(select(cls).where(cls.santo_id == santo_id).order_by(cls.titulo)))

    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "titulo", "autor")
        santo_id = dados.get("santo_id")
        _validar_santo(session, santo_id)
        livro = cls(titulo=dados["titulo"], autor=dados["autor"], resumo=dados.get("resumo"),
                    contexto_historico=dados.get("contexto_historico"),
                    livro_recomendado=bool(dados.get("livro_recomendado", False)),
                    santo_id=santo_id)
        _persistir(session, livro, f"o livro '{dados['titulo']}' de {dados['autor']}")
        return livro

    @classmethod
    def atualizar(cls, session, id_livro: int, dados: dict, token: str):
        _exigir_autenticacao(token)
        _validar_alteracoes(
            dados, {"titulo", "autor", "resumo", "contexto_historico", "livro_recomendado", "santo_id"},
            obrigatorios=("titulo", "autor"))
        livro = _buscar_ou_erro(session, cls, id_livro, "Livro")
        if "santo_id" in dados:
            _validar_santo(session, dados["santo_id"])
        for campo, valor in dados.items():
            setattr(livro, campo, bool(valor) if campo == "livro_recomendado" else valor)
        _persistir(session, livro, f"o livro '{livro.titulo}' de {livro.autor}")
        return livro

    @classmethod
    def excluir(cls, session, id_livro: int, token: str) -> None:
        _exigir_autenticacao(token)
        livro = _buscar_ou_erro(session, cls, id_livro, "Livro")
        _remover(session, livro, f"o livro '{livro.titulo}'")


# --------------------------------------------------------------------------- #
# Agenda
# --------------------------------------------------------------------------- #
class Agenda(Base):
    """Período agendado pelo Administrador: de uma novena ou da liturgia.

    * NOVENA: dia 1 em ``data_inicio``; ``data_fim`` = início + 8 dias (calculado
      pelos métodos). O "Dia X de 9" é derivado (``calcular_dia_atual``).
    * LITURGIA: janela de dias de liturgia cadastrados (UC14).

    A associação Agenda 0..* — 0..1 Novena é materializada pela coluna
    ``id_novena`` (a UML não mostra o atributo, mas os métodos usam ``novena_id``).

    "Ativa" nas consultas = status ATIVA e período ainda não encerrado. Uma agenda
    ATIVA cujo período já terminou é tratada como encerrada e passa a CONCLUIDA
    quando a mesma novena é agendada de novo.
    """

    __tablename__ = "Agendas"
    __table_args__ = (
        CheckConstraint("data_fim_agenda >= data_inicio_agenda", name="ck_agenda_periodo"),
        CheckConstraint("tipo_agenda = 'NOVENA' OR id_novena IS NULL",
                        name="ck_agenda_novena_so_no_tipo_novena"),
        # No máximo uma agenda ATIVA por novena.
        Index("uq_agenda_ativa_por_novena", "id_novena", unique=True,
              sqlite_where=text("status_agenda = 'ATIVA' AND id_novena IS NOT NULL"),
              postgresql_where=text("status_agenda = 'ATIVA' AND id_novena IS NOT NULL")),
    )

    id = Column("id_agenda", Integer, primary_key=True)
    tipo = Column("tipo_agenda", Enum(TipoAgenda), nullable=False)
    data_inicio = Column("data_inicio_agenda", Date, nullable=False)
    data_fim = Column("data_fim_agenda", Date, nullable=False)
    status = Column("status_agenda", Enum(StatusAgenda), nullable=False, default=StatusAgenda.ATIVA)
    novena_id = Column("id_novena", Integer, ForeignKey("Novenas.id_novena", ondelete="SET NULL"),
                       index=True)

    novena = relationship("Novena", back_populates="agendas")
    liturgias_dia = relationship("LiturgiaDia", back_populates="agenda", order_by="LiturgiaDia.data")
    liturgias_hora = relationship("LiturgiaHora", back_populates="agenda",
                                  order_by="LiturgiaHora.data")

    # -- regra de janela da liturgia (RNF07); '#' (protegido) na UML --
    @staticmethod
    def _dentro_intervalo(data: date, hoje: date | None = None) -> bool:
        hoje = hoje or date.today()
        return abs((data - hoje).days) <= INTERVALO_LITURGIA_DIAS

    @classmethod
    def _validar_intervalo(cls, data: date) -> None:
        if not cls._dentro_intervalo(data):
            raise ForaDoIntervaloError()

    # -- escrita (Administrador) --
    @classmethod
    def agendar_novena(cls, session, novena_id: int, data_inicio, token: str):
        """UC06: agenda a novena com dia 1 em ``data_inicio`` (fim = início + 8)."""
        _exigir_autenticacao(token)
        _buscar_ou_erro(session, Novena, novena_id, "Novena")
        inicio = _converter_data(data_inicio, "data_inicio")
        hoje = date.today()
        for anterior in session.scalars(select(cls).where(
                cls.novena_id == novena_id, cls.status == StatusAgenda.ATIVA)):
            if anterior.data_fim < hoje:
                anterior.status = StatusAgenda.CONCLUIDA  # período já encerrado
            else:
                raise RegistroDuplicadoError(
                    "Esta novena já tem uma agenda ativa. Cancele-a (cancelar) ou "
                    "reprograme-a (atualizar_progresso).")
        session.flush()
        agenda = cls(tipo=TipoAgenda.NOVENA, novena_id=novena_id, data_inicio=inicio,
                     data_fim=inicio + timedelta(days=DIAS_DA_NOVENA - 1),
                     status=StatusAgenda.ATIVA)
        _persistir(session, agenda, "uma agenda ativa para esta novena")
        return agenda

    def atualizar_progresso(self, nova_data_inicio, token: str) -> None:
        """UC10: reprograma o dia 1 da novena (e, com ele, o fim)."""
        _exigir_autenticacao(token)
        if self.tipo != TipoAgenda.NOVENA:
            raise DadosInvalidosError("Só agendas de novena têm progresso.")
        if self.status != StatusAgenda.ATIVA:
            raise DadosInvalidosError("Só agendas ativas podem ser reprogramadas.")
        inicio = _converter_data(nova_data_inicio, "nova_data_inicio")
        self.data_inicio = inicio
        self.data_fim = inicio + timedelta(days=DIAS_DA_NOVENA - 1)
        _persistir(_sessao_de(self), self, "uma agenda ativa para esta novena")

    def cancelar(self, token: str) -> None:
        """UC07: cancela a agenda sem apagar o registro."""
        _exigir_autenticacao(token)
        if self.status != StatusAgenda.ATIVA:
            raise DadosInvalidosError("Só agendas ativas podem ser canceladas.")
        self.status = StatusAgenda.CANCELADA
        _persistir(_sessao_de(self), self, "esta agenda")

    @classmethod
    def agendar_liturgias(cls, session, data_inicio, data_fim, token: str):
        """UC14: registra a janela de dias de liturgia disponíveis."""
        _exigir_autenticacao(token)
        inicio = _converter_data(data_inicio, "data_inicio")
        fim = _converter_data(data_fim, "data_fim")
        if fim < inicio:
            raise DadosInvalidosError("A data final não pode ser anterior à data inicial.")
        agenda = cls(tipo=TipoAgenda.LITURGIA, data_inicio=inicio, data_fim=fim,
                     status=StatusAgenda.ATIVA)
        _persistir(session, agenda, "esta agenda de liturgia")
        return agenda

    # -- leitura (pública) --
    @classmethod
    def buscar_ativa(cls, session, novena_id: int, hoje: date | None = None):
        """UC08: agenda em andamento (ou futura) da novena; ``None`` se não houver."""
        hoje = hoje or date.today()
        return session.scalar(
            select(cls).where(cls.novena_id == novena_id, cls.status == StatusAgenda.ATIVA,
                              cls.data_fim >= hoje)
            .order_by(cls.data_inicio, cls.id))

    def calcular_dia_atual(self, hoje: date | None = None) -> int:
        """US08: "Dia X de 9". Devolve 1-9 durante a novena e 0 fora dela.

        0 significa: ainda não começou, já terminou ou foi cancelada. Valor
        derivado, não persistido.
        """
        if self.tipo != TipoAgenda.NOVENA:
            raise DadosInvalidosError("Só agendas de novena têm dia atual.")
        if self.status != StatusAgenda.ATIVA:
            return 0
        hoje = hoje or date.today()
        dia = (hoje - self.data_inicio).days + 1
        return dia if 1 <= dia <= DIAS_DA_NOVENA else 0

    @classmethod
    def listar_ativas(cls, session, tipo, hoje: date | None = None):
        """UC05: agendas ativas (em andamento ou futuras) do tipo informado."""
        tipo = _converter_enum(TipoAgenda, tipo, "tipo")
        hoje = hoje or date.today()
        return list(session.scalars(
            select(cls).where(cls.tipo == tipo, cls.status == StatusAgenda.ATIVA,
                              cls.data_fim >= hoje)
            .order_by(cls.data_inicio, cls.id)))


# --------------------------------------------------------------------------- #
# Liturgia: LiturgiaDia e LiturgiaHora (classes independentes, como na UML)
# --------------------------------------------------------------------------- #
def _validar_agenda_liturgia(session, agenda_id, data: date) -> None:
    """Toda liturgia pertence a uma agenda de LITURGIA ativa que cubra a data."""
    agenda = session.get(Agenda, agenda_id) if agenda_id is not None else None
    if agenda is None:
        raise DadosInvalidosError(f"Agenda {agenda_id} não encontrada.")
    if agenda.tipo != TipoAgenda.LITURGIA:
        raise DadosInvalidosError("A agenda informada não é de liturgia.")
    if agenda.status != StatusAgenda.ATIVA:
        raise DadosInvalidosError("A agenda de liturgia informada não está ativa.")
    if not agenda.data_inicio <= data <= agenda.data_fim:
        raise DadosInvalidosError(
            f"A data {data.isoformat()} está fora do período da agenda "
            f"({agenda.data_inicio.isoformat()} a {agenda.data_fim.isoformat()}).")


def _consulta_liturgia_visivel(modelo, data: date):
    """Registros da data cuja agenda não foi cancelada."""
    return (select(modelo).join(modelo.agenda)
            .where(modelo.data == data, Agenda.status != StatusAgenda.CANCELADA))


class LiturgiaDia(Base):
    __tablename__ = "Liturgia_Dia"

    id = Column("id_liturgia_dia", Integer, primary_key=True)
    agenda_id = Column("id_agenda", Integer, ForeignKey("Agendas.id_agenda"), nullable=False,
                       index=True)
    # No máximo uma Liturgia do Dia por data.
    data = Column("data_liturgia_dia", Date, nullable=False, unique=True)
    santo_celebrado = Column("santo_celebrado_liturgia_dia", Text)
    primeira_leitura = Column("primeira_leitura_liturgia_dia", Text)
    salmo = Column("salmo_liturgia_dia", Text)
    evangelho = Column("evangelho_liturgia_dia", Text)
    segunda_leitura = Column("segunda_leitura_liturgia_dia", Text)  # domingos/festividades

    agenda = relationship("Agenda", back_populates="liturgias_dia")

    CAMPOS_TEXTO = ("santo_celebrado", "primeira_leitura", "salmo", "evangelho", "segunda_leitura")

    @classmethod
    def buscar_data(cls, session, data: date):
        Agenda._validar_intervalo(data)
        return session.scalar(_consulta_liturgia_visivel(cls, data))

    def possui_segunda_leitura(self) -> bool:
        return bool(self.segunda_leitura and self.segunda_leitura.strip())

    # -- escrita (UC09; no MVP a liturgia vem dos seeds) --
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "data", "agenda_id")
        dia = _converter_data(dados["data"])
        _validar_agenda_liturgia(session, dados["agenda_id"], dia)
        registro = cls(data=dia, agenda_id=dados["agenda_id"],
                       **{campo: dados.get(campo) for campo in cls.CAMPOS_TEXTO})
        _persistir(session, registro, f"uma Liturgia do Dia em {dia.isoformat()}")
        return registro

    @classmethod
    def atualizar(cls, session, id_liturgia_dia: int, dados: dict, token: str):
        _exigir_autenticacao(token)
        _validar_alteracoes(dados, {"data", "agenda_id", *cls.CAMPOS_TEXTO},
                            obrigatorios=("data", "agenda_id"))
        registro = _buscar_ou_erro(session, cls, id_liturgia_dia, "Liturgia do Dia")
        nova_data = _converter_data(dados["data"]) if "data" in dados else registro.data
        nova_agenda = dados.get("agenda_id", registro.agenda_id)
        if "data" in dados or "agenda_id" in dados:
            _validar_agenda_liturgia(session, nova_agenda, nova_data)
        registro.data, registro.agenda_id = nova_data, nova_agenda
        for campo in cls.CAMPOS_TEXTO:
            if campo in dados:
                setattr(registro, campo, dados[campo])
        _persistir(session, registro, f"uma Liturgia do Dia em {nova_data.isoformat()}")
        return registro

    @classmethod
    def excluir(cls, session, id_liturgia_dia: int, token: str) -> None:
        _exigir_autenticacao(token)
        registro = _buscar_ou_erro(session, cls, id_liturgia_dia, "Liturgia do Dia")
        _remover(session, registro, f"a Liturgia do Dia de {registro.data.isoformat()}")


class LiturgiaHora(Base):
    __tablename__ = "Liturgia_Hora"
    __table_args__ = (
        # No máximo um registro por bloco canônico em cada data.
        UniqueConstraint("data_liturgia_hora", "bloco_liturgia_hora",
                         name="uq_liturgia_hora_data_bloco"),
    )

    id = Column("id_liturgia_hora", Integer, primary_key=True)
    agenda_id = Column("id_agenda", Integer, ForeignKey("Agendas.id_agenda"), nullable=False,
                       index=True)
    data = Column("data_liturgia_hora", Date, nullable=False, index=True)
    bloco = Column("bloco_liturgia_hora", Enum(BlocoLiturgia), nullable=False)
    texto = Column("texto_liturgia_hora", Text, nullable=False)

    agenda = relationship("Agenda", back_populates="liturgias_hora")

    @classmethod
    def buscar_data(cls, session, data: date):
        Agenda._validar_intervalo(data)
        return list(session.scalars(_consulta_liturgia_visivel(cls, data).order_by(cls.id)))

    @classmethod
    def buscar_bloco(cls, session, data: date, bloco):
        Agenda._validar_intervalo(data)
        bloco = _converter_enum(BlocoLiturgia, bloco, "bloco")
        return session.scalar(_consulta_liturgia_visivel(cls, data).where(cls.bloco == bloco))

    # -- escrita (UC09; no MVP a liturgia vem dos seeds) --
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "data", "agenda_id", "bloco", "texto")
        dia = _converter_data(dados["data"])
        bloco = _converter_enum(BlocoLiturgia, dados["bloco"], "bloco")
        _validar_agenda_liturgia(session, dados["agenda_id"], dia)
        registro = cls(data=dia, agenda_id=dados["agenda_id"], bloco=bloco, texto=dados["texto"])
        _persistir(session, registro, f"um registro de {bloco.value} em {dia.isoformat()}")
        return registro

    @classmethod
    def atualizar(cls, session, id_liturgia_hora: int, dados: dict, token: str):
        _exigir_autenticacao(token)
        _validar_alteracoes(dados, {"data", "agenda_id", "bloco", "texto"},
                            obrigatorios=("data", "agenda_id", "bloco", "texto"))
        registro = _buscar_ou_erro(session, cls, id_liturgia_hora, "Liturgia das Horas")
        nova_data = _converter_data(dados["data"]) if "data" in dados else registro.data
        nova_agenda = dados.get("agenda_id", registro.agenda_id)
        if "data" in dados or "agenda_id" in dados:
            _validar_agenda_liturgia(session, nova_agenda, nova_data)
        registro.data, registro.agenda_id = nova_data, nova_agenda
        if "bloco" in dados:
            registro.bloco = _converter_enum(BlocoLiturgia, dados["bloco"], "bloco")
        if "texto" in dados:
            registro.texto = dados["texto"]
        _persistir(session, registro,
                   f"um registro de {registro.bloco.value} em {nova_data.isoformat()}")
        return registro

    @classmethod
    def excluir(cls, session, id_liturgia_hora: int, token: str) -> None:
        _exigir_autenticacao(token)
        registro = _buscar_ou_erro(session, cls, id_liturgia_hora, "Liturgia das Horas")
        _remover(session, registro, f"o registro de {registro.bloco.value} de {registro.data.isoformat()}")

"""Modelos do FIDES, traduzidos do Diagrama de Classes.

Convenções (seguindo o database.db do projeto anterior):
  * tabelas com inicial maiúscula (Santos, Oracoes, Dias_Novena...);
  * colunas no formato ``campo_entidade`` e chaves ``id_entidade`` (a FK tem o
    mesmo nome da PK que referencia);
  * herança por tabela unida (joined table) para Liturgia -> LiturgiaHora/Dia,
    do mesmo jeito que Clientes -> Lojas/Consumidor_Final;
  * enums gravados como VARCHAR.

Os atributos Python seguem os nomes do diagrama (``santo.nome``,
``oracao.santo_id``...), enquanto o nome físico da coluna segue a convenção
acima (``Column("nome_santo", ...)``).

Sobre transações: os métodos ``cadastrar`` fazem ``add`` + ``flush`` e NÃO dão
``commit``. Quem chama (a rota da API) decide quando confirmar a transação.
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
from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import relationship, validates

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
    """Dados de cadastro incompletos ou inconsistentes."""


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
    AO_ACORDAR = "Ao acordar"
    REFEICOES = "Refeições"
    MISSA = "Missa"
    ANTES_DE_DORMIR = "Antes de dormir"


class BlocoLiturgia(enum.Enum):
    LAUDES = "Laudes"
    HORAS_MEDIAS = "Horas médias"
    VESPERAS = "Vésperas"


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
    Column("id_oracao", Integer, ForeignKey("Oracoes.id_oracao"), primary_key=True),
    Column("id_momento_dia", Integer, ForeignKey("Momentos_Dia.id_momento_dia"), primary_key=True),
)

Oracao_Dia_Novena = Table(
    "Oracao_Dia_Novena",
    Base.metadata,
    Column("id_dia_novena", Integer, ForeignKey("Dias_Novena.id_dia_novena"), primary_key=True),
    Column("id_oracao", Integer, ForeignKey("Oracoes.id_oracao"), primary_key=True),
)


# --------------------------------------------------------------------------- #
# Administrador
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
    def _validar_token(token) -> bool:  # '#' no diagrama = protegido
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
    # Coluna auxiliar (não está no diagrama): nome sem acento/minúsculo, usada
    # apenas por buscar_nome(). É preenchida automaticamente.
    nome_busca = Column("nome_busca_santo", String, index=True)
    foto_url = Column("foto_url_santo", String)
    biografia = Column("biografia_santo", Text)

    oracoes = relationship("Oracao", back_populates="santo", cascade="all, delete-orphan",
                           order_by="Oracao.titulo")
    novenas = relationship("Novena", back_populates="santo", cascade="all, delete-orphan",
                           order_by="Novena.titulo")
    livros = relationship("Livro", back_populates="santo", cascade="all, delete-orphan",
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

    def obter_oracoes(self):
        return list(self.oracoes)

    def obter_novena(self):
        return list(self.novenas)

    def obter_livro(self):
        return list(self.livros)

    # -- escrita (protegida, RNF05) --
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "nome")
        santo = cls(nome=dados["nome"], foto_url=dados.get("foto_url"),
                    biografia=dados.get("biografia"))
        session.add(santo)
        session.flush()
        return santo


# --------------------------------------------------------------------------- #
# Momento do dia
# --------------------------------------------------------------------------- #
class MomentoDia(Base):
    __tablename__ = "Momentos_Dia"

    id = Column("id_momento_dia", Integer, primary_key=True)
    bloco = Column("bloco_momento_dia", Enum(BlocoMomento), nullable=False, unique=True)

    oracoes = relationship("Oracao", secondary=Oracao_Momento_Dia, back_populates="momentos")

    @classmethod
    def listar_todos(cls, session):
        return list(session.scalars(select(cls).order_by(cls.id)))


# --------------------------------------------------------------------------- #
# Oração
# --------------------------------------------------------------------------- #
class Oracao(Base):
    __tablename__ = "Oracoes"

    id = Column("id_oracao", Integer, primary_key=True)
    titulo = Column("titulo_oracao", String, nullable=False)
    texto = Column("texto_oracao", Text, nullable=False)
    basica = Column("basica_oracao", Boolean, nullable=False, default=False)
    # Nulo para orações gerais (ex.: Pai Nosso), que não pertencem a um santo.
    santo_id = Column("id_santo", Integer, ForeignKey("Santos.id_santo"))

    santo = relationship("Santo", back_populates="oracoes")
    momentos = relationship("MomentoDia", secondary=Oracao_Momento_Dia, back_populates="oracoes")
    dias_novena = relationship("DiaNovena", secondary=Oracao_Dia_Novena, back_populates="oracoes")

    # -- leitura --
    @classmethod
    def listar_todas(cls, session, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
        return list(session.scalars(_paginar(select(cls).order_by(cls.titulo), pagina, limite)))

    @classmethod
    def listar_basicas(cls, session, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
        consulta = select(cls).where(cls.basica.is_(True)).order_by(cls.id)
        return list(session.scalars(_paginar(consulta, pagina, limite)))

    @classmethod
    def filtrar_momento(cls, session, momento_id: int, pagina: int = 1,
                        limite: int = LIMITE_MAXIMO_POR_PAGINA):
        consulta = (select(cls).join(cls.momentos).where(MomentoDia.id == momento_id)
                    .order_by(cls.titulo))
        return list(session.scalars(_paginar(consulta, pagina, limite)))

    @classmethod
    def buscar_por_santo(cls, session, santo_id: int):
        return list(session.scalars(select(cls).where(cls.santo_id == santo_id).order_by(cls.titulo)))

    # -- escrita --
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "titulo", "texto")
        santo_id = dados.get("santo_id")
        if santo_id is not None and session.get(Santo, santo_id) is None:
            raise DadosInvalidosError(f"Santo {santo_id} não encontrado.")
        oracao = cls(titulo=dados["titulo"], texto=dados["texto"],
                     basica=bool(dados.get("basica", False)), santo_id=santo_id)
        session.add(oracao)
        if dados.get("momentos_ids"):
            momentos = list(session.scalars(
                select(MomentoDia).where(MomentoDia.id.in_(dados["momentos_ids"]))))
            oracao.categorizar(momentos, token)
        session.flush()
        return oracao

    def categorizar(self, momentos, token: str) -> None:
        """Define (substitui) os momentos do dia em que a oração é indicada."""
        _exigir_autenticacao(token)
        self.momentos = list(momentos)


# --------------------------------------------------------------------------- #
# Novena e Dia_Novena
# --------------------------------------------------------------------------- #
class Novena(Base):
    __tablename__ = "Novenas"

    id = Column("id_novena", Integer, primary_key=True)
    titulo = Column("titulo_novena", String, nullable=False)
    descricao = Column("descricao_novena", Text)
    santo_id = Column("id_santo", Integer, ForeignKey("Santos.id_santo"), nullable=False)

    santo = relationship("Santo", back_populates="novenas")
    dias = relationship("DiaNovena", back_populates="novena", cascade="all, delete-orphan",
                        order_by="DiaNovena.numero_dia")

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
        """
        _exigir_autenticacao(token)
        _exigir_campos(dados, "titulo", "santo_id")
        dias = dados.get("dias") or []
        if len(dias) != DIAS_DA_NOVENA:
            raise DadosInvalidosError(f"Uma novena precisa ter exatamente {DIAS_DA_NOVENA} dias.")
        if session.get(Santo, dados["santo_id"]) is None:
            raise DadosInvalidosError(f"Santo {dados['santo_id']} não encontrado.")

        novena = cls(titulo=dados["titulo"], descricao=dados.get("descricao"),
                     santo_id=dados["santo_id"])
        with session.no_autoflush:  # a novena ainda está sendo montada fora da sessão
            for numero, dia in enumerate(dias, start=1):
                _exigir_campos(dia, "texto_reflexao")
                item = DiaNovena(numero_dia=numero, texto_reflexao=dia["texto_reflexao"])
                ids = dia.get("oracoes_base_ids")
                if ids:
                    item.oracoes = list(session.scalars(select(Oracao).where(Oracao.id.in_(ids))))
                novena.dias.append(item)
        session.add(novena)
        session.flush()
        return novena


class DiaNovena(Base):
    __tablename__ = "Dias_Novena"
    __table_args__ = (
        UniqueConstraint("id_novena", "numero_dia_novena", name="uq_dia_novena_numero"),
        CheckConstraint("numero_dia_novena BETWEEN 1 AND 9", name="ck_dia_novena_intervalo"),
    )

    id = Column("id_dia_novena", Integer, primary_key=True)
    novena_id = Column("id_novena", Integer, ForeignKey("Novenas.id_novena"), nullable=False)
    numero_dia = Column("numero_dia_novena", Integer, nullable=False)
    texto_reflexao = Column("texto_reflexao_dia_novena", Text, nullable=False)

    novena = relationship("Novena", back_populates="dias")
    # Orações base do dia (Pai Nosso, Ave Maria...) - N..N com Oração.
    oracoes = relationship("Oracao", secondary=Oracao_Dia_Novena, back_populates="dias_novena")

    @classmethod
    def buscar_novena_dia(cls, session, novena_id: int, dia: int):
        return session.scalar(
            select(cls).where(cls.novena_id == novena_id, cls.numero_dia == dia))

    @classmethod
    def listar_novena(cls, session, novena_id: int):
        return list(session.scalars(
            select(cls).where(cls.novena_id == novena_id).order_by(cls.numero_dia)))

    def oracoes_base(self):
        return list(self.oracoes)


# --------------------------------------------------------------------------- #
# Livro
# --------------------------------------------------------------------------- #
class Livro(Base):
    __tablename__ = "Livros"

    id = Column("id_livro", Integer, primary_key=True)
    titulo = Column("titulo_livro", String, nullable=False)
    autor = Column("autor_livro", String, nullable=False)
    resumo = Column("resumo_livro", Text)
    contexto_historico = Column("contexto_historico_livro", Text)
    # Nulo para obras gerais que não estão ligadas a um santo (ex.: Scott Hahn).
    santo_id = Column("id_santo", Integer, ForeignKey("Santos.id_santo"))

    santo = relationship("Santo", back_populates="livros")

    @classmethod
    def listar_todos(cls, session, pagina: int = 1, limite: int = LIMITE_MAXIMO_POR_PAGINA):
        return list(session.scalars(_paginar(select(cls).order_by(cls.titulo), pagina, limite)))

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
        if santo_id is not None and session.get(Santo, santo_id) is None:
            raise DadosInvalidosError(f"Santo {santo_id} não encontrado.")
        livro = cls(titulo=dados["titulo"], autor=dados["autor"], resumo=dados.get("resumo"),
                    contexto_historico=dados.get("contexto_historico"), santo_id=santo_id)
        session.add(livro)
        session.flush()
        return livro


# --------------------------------------------------------------------------- #
# Liturgia (abstrata) -> LiturgiaHora / LiturgiaDia
# --------------------------------------------------------------------------- #
class Liturgia(Base):
    """Classe abstrata: guarda apenas id e data; não é instanciada diretamente."""

    __tablename__ = "Liturgia"

    id = Column("id_liturgia", Integer, primary_key=True)
    data = Column("data_liturgia", Date, nullable=False, index=True)
    tipo = Column("tipo_liturgia", String(10), nullable=False)

    __mapper_args__ = {"polymorphic_on": tipo}

    def __init__(self, **kwargs):
        if type(self) is Liturgia:
            raise TypeError("Liturgia é abstrata: use LiturgiaHora ou LiturgiaDia.")
        super().__init__(**kwargs)

    @staticmethod
    def _dentro_intervalo(data: date, hoje: date | None = None) -> bool:  # protegido
        hoje = hoje or date.today()
        return abs((data - hoje).days) <= INTERVALO_LITURGIA_DIAS

    @classmethod
    def _validar_intervalo(cls, data: date) -> None:
        if not cls._dentro_intervalo(data):
            raise ForaDoIntervaloError()

    @classmethod
    def buscar_por_data(cls, session, data: date):
        """Todos os registros litúrgicos da data (horas + liturgia do dia)."""
        cls._validar_intervalo(data)
        return list(session.scalars(select(cls).where(cls.data == data).order_by(cls.id)))


class LiturgiaHora(Liturgia):
    __tablename__ = "Liturgia_Hora"

    id = Column("id_liturgia", Integer, ForeignKey("Liturgia.id_liturgia"), primary_key=True)
    bloco = Column("bloco_liturgia_hora", Enum(BlocoLiturgia), nullable=False)
    texto = Column("texto_liturgia_hora", Text, nullable=False)

    __mapper_args__ = {"polymorphic_identity": "hora"}

    @classmethod
    def buscar_data(cls, session, data: date):
        cls._validar_intervalo(data)
        return list(session.scalars(select(cls).where(cls.data == data).order_by(cls.id)))

    @classmethod
    def buscar_bloco(cls, session, data: date, bloco):
        cls._validar_intervalo(data)
        if isinstance(bloco, str):
            bloco = BlocoLiturgia[bloco.upper()]
        return session.scalar(select(cls).where(cls.data == data, cls.bloco == bloco))


class LiturgiaDia(Liturgia):
    __tablename__ = "Liturgia_Dia"

    id = Column("id_liturgia", Integer, ForeignKey("Liturgia.id_liturgia"), primary_key=True)
    santo_celebrado = Column("santo_celebrado_liturgia_dia", String)
    primeira_leitura = Column("primeira_leitura_liturgia_dia", String)
    salmo = Column("salmo_liturgia_dia", String)
    evangelho = Column("evangelho_liturgia_dia", String)
    segunda_leitura = Column("segunda_leitura_liturgia_dia", Text)  # só domingos/festas

    __mapper_args__ = {"polymorphic_identity": "dia"}

    @classmethod
    def buscar_data(cls, session, data: date):
        cls._validar_intervalo(data)
        return session.scalar(select(cls).where(cls.data == data))

    def possui_segunda_leitura(self) -> bool:
        return bool(self.segunda_leitura and self.segunda_leitura.strip())

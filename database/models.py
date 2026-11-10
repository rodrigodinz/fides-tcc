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

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Constantes do negócio (RNFs)
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
Limite_Maximo_Por_Pagina = 20
Periodo_Disponivel_De_Liturgias = 7
Dias_Da_Novena = 9
Periodo_De_Validade_Do_Token_Adm = 3600
Senha_Secreta_Adm = os.getenv("FIDES_SECRET_KEY", "dev-only-troque-em-producao")


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# Exceções de domínio
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
class Erro_De_Autenticacao(Exception):
    pass


class Erro_De_Dados_Incorretos(ValueError):
    pass


class Erro_De_Registros_Duplicados(Erro_De_Dados_Incorretos):
    pass


class Erro_De_Registro_Nao_Encontrado(Erro_De_Dados_Incorretos):
    pass


class Erro_Da_Liturgia_Fora_Da_Data_Permitida(ValueError):
    # mensagem fixa mostrada quando a data sai da janela de ±7 dias
    def __init__(self):
        super().__init__(
            "Esta data está fora do intervalo disponível na fase 1 do Fides."
        )


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Enums
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
class BlocoMomento(enum.Enum):
    AO_ACORDAR = "Ao acordar"
    REFEICOES = "Refeições"
    MISSA = "Missa"
    ANTES_DE_DORMIR = "Antes de dormir"


class BlocoLiturgia(enum.Enum):
    LAUDES = "Laudes"
    HORAS_MEDIAS = "Horas médias"
    VESPERAS = "Vésperas"


class TipoAgenda(enum.Enum):
    NOVENA = "Novena"
    LITURGIA = "Liturgia"


class StatusAgenda(enum.Enum):
    ATIVA = "Ativa"
    CANCELADA = "Cancelada"
    CONCLUIDA = "Concluída"


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Normalizações do Código
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# tira acentos e deixa minúsculo, pra busca por nome ignorar acentuação
def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sem_acento.lower().strip()


# aplica limit/offset na consulta, respeitando o máximo de 20 itens por página
def _paginar(consulta, pagina: int = 1, limite: int = Limite_Maximo_Por_Pagina):
    pagina = max(int(pagina), 1)
    limite = min(max(int(limite), 1), Limite_Maximo_Por_Pagina)
    return consulta.limit(limite).offset((pagina - 1) * limite)


# barra o cadastro quando falta algum campo obrigatório
def _exigir_campos(dados: dict, *campos: str) -> None:
    faltando = [campo for campo in campos if not dados.get(campo)]
    if faltando:
        raise Erro_De_Dados_Incorretos(f"Campos obrigatórios que estão faltando: {', '.join(faltando)}")


# confere se a atualização só mexe em campos permitidos e não esvazia os obrigatórios
def _validar_alteracoes(dados, editaveis, obrigatorios=()) -> None:
    if not isinstance(dados, dict) or not dados:
        raise Erro_De_Dados_Incorretos("Informe ao menos um campo para atualizar.")
    desconhecidos = sorted(set(dados) - set(editaveis))
    if desconhecidos:
        raise Erro_De_Dados_Incorretos(f"Campos desconhecidos: {', '.join(desconhecidos)}")
    vazios = [campo for campo in obrigatorios if campo in dados and not dados[campo]]
    if vazios:
        raise Erro_De_Dados_Incorretos(f"Campos obrigatórios não podem ficar vazios, Johnson: {', '.join(vazios)}")


# grava no banco (flush) e traduz erro de UNIQUE em Erro_De_Registros_Duplicados
def _persistir(session, objeto, descricao: str) -> None:
    session.add(objeto)
    try:
        session.flush()
    except IntegrityError as erro:
        mensagem = str(erro.orig).upper()
        if "UNIQUE" in mensagem or "DUPLICATE" in mensagem:
            raise Erro_De_Registros_Duplicados(f"Já existe {descricao}.") from erro
        raise


# apaga do banco e traduz os erros de integridade em mensagens de domínio
def _remover(session, objeto, descricao: str) -> None:
    session.delete(objeto)
    try:
        session.flush()
    except IntegrityError as erro:
        mensagem = str(erro.orig).upper()
        if "UNIQUE" in mensagem or "DUPLICATE" in mensagem:
            raise Erro_De_Registros_Duplicados(
                f"Não foi possível excluir {descricao}: a exclusão deixaria um título repetido.") from erro
        if "FOREIGN KEY" in mensagem:
            raise Erro_De_Dados_Incorretos(
                f"Não foi possível excluir {descricao}: há registros vinculados.") from erro
        raise


# recupera a sessão do SQLAlchemy onde o objeto tá ligado
def _sessao_de(objeto):
    session = object_session(objeto)
    if session is None:
        raise Erro_De_Dados_Incorretos("O registro precisa estar associado a uma sessão do banco")
    return session


# busca pelo id e lança Erro_De_Registro_Nao_Encontrado se não existir
def _buscar_ou_erro(session, modelo, id_registro, nome: str):
    registro = session.get(modelo, id_registro) if id_registro is not None else None
    if registro is None:
        raise Erro_De_Registro_Nao_Encontrado(f"{nome} {id_registro} não encontrado")
    return registro


# garante que o santo informado existe antes de vincular
def _validar_santo(session, santo_id) -> None:
    if santo_id is not None and session.get(Santo, santo_id) is None:
        raise Erro_De_Dados_Incorretos(f"Santo {santo_id} não encontrado")


# aceita date, datetime ou texto AAAA-MM-DD e devolve sempre um date
def _converter_data(valor, campo: str = "data") -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, str):
        try:
            return date.fromisoformat(valor)
        except ValueError:
            pass
    raise Erro_De_Dados_Incorretos(f"O campo '{campo}' deve ser uma data Ano-Mes-Dia.")


# converte texto no enum correspondente
def _converter_enum(tipo_enum, valor, campo: str):
    if isinstance(valor, tipo_enum):
        return valor
    if isinstance(valor, str):
        try:
            return tipo_enum[valor.strip().upper()]
        except KeyError:
            pass
    opcoes = ", ".join(membro.name for membro in tipo_enum)
    raise Erro_De_Dados_Incorretos(f"Valor inválido para '{campo}'. Opções: {opcoes}.")


# carrega as orações pelos ids, mantendo a ordem e acusando ids que não existem
def _buscar_oracoes(session, ids) -> list:
    ids = list(dict.fromkeys(ids or []))
    if not ids:
        return []
    with session.no_autoflush:
        encontradas = list(session.scalars(select(Oracao).where(Oracao.id.in_(ids))))
    faltando = sorted(set(ids) - {oracao.id for oracao in encontradas})
    if faltando:
        raise Erro_De_Dados_Incorretos(f"Orações não encontradas: {faltando}")
    oracoes_por_id = {oracao.id: oracao for oracao in encontradas}
    return [oracoes_por_id[id_oracao] for id_oracao in ids]


# transforma ids, textos ou enums nos objetos MomentoDia do banco
def _resolver_momentos(session, itens) -> list:
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
                raise Erro_De_Dados_Incorretos(f"Momento do dia não cadastrado: {item!r}")
            if momento not in resultado:
                resultado.append(momento)
    return resultado


# toda operação de escresver do adm passa por aqui
def _exigir_autenticacao(token) -> None:
    if not Administrador._validar_token(token):
        raise Erro_De_Autenticacao("Token expirado.")


# gera o hash PBKDF2-SHA256 com salt aleatório; a senha nunca é salva em texto
def _hash_senha(senha: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    iteracoes = 200_000
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), iteracoes)
    return f"pbkdf2_sha256${iteracoes}${salt}${digest.hex()}"


# compara a senha digitada com o hash salvo
def _verificar_senha(senha: str, armazenado: str) -> bool:
    try:
        _, iteracoes, salt, esperado = armazenado.split("$")
        digest = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(salt), int(iteracoes))
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(digest.hex(), esperado)


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


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Administrador
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
class Administrador(Base):
    __tablename__ = "Administradores"

    id = Column("id_administrador", Integer, primary_key=True)
    nome = Column("nome_administrador", String, nullable=False)
    login = Column("login_administrador", String, nullable=False, unique=True)
    email = Column("email_administrador", String, unique=True)
    senha_hash = Column("senha_hash_administrador", String, nullable=False)

    # troca a senha do administrador (guarda só o hash)
    def definir_senha(self, senha: str) -> None:
        self.senha_hash = _hash_senha(senha)

    # cria o token assinado (HMAC) que vale por 1 hora
    def emitir_token(self) -> str:
        payload = {"sub": self.id, "exp": int(time.time()) + Periodo_De_Validade_Do_Token_Adm}
        corpo = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        assinatura = hmac.new(Senha_Secreta_Adm.encode(), corpo.encode(), hashlib.sha256).hexdigest()
        return f"{corpo}.{assinatura}"

    # confere login/e-mail e senha e devolve um token novo
    @classmethod
    def autenticar(cls, session, login: str, senha: str) -> str:
        admin = None
        if login:
            login = login.strip()
            admin = session.scalar(select(cls).where(cls.login == login))
            if admin is None:
                admin = session.scalar(select(cls).where(cls.email == login))
        hash_alvo = admin.senha_hash if admin else _hash_senha("senha-inexistente")
        if not _verificar_senha(senha or "", hash_alvo) or admin is None:
            raise Erro_De_Autenticacao("Login ou senha inválidos.")
        return admin.emitir_token()

    # confere a assinatura e a validade do token
    @staticmethod
    def _validar_token(token) -> bool:
        try:
            corpo, assinatura = token.split(".")
            esperada = hmac.new(Senha_Secreta_Adm.encode(), corpo.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(assinatura, esperada):
                return False
            payload = json.loads(base64.urlsafe_b64decode(corpo.encode()))
            return payload["exp"] > time.time()
        except (ValueError, KeyError, AttributeError, TypeError):
            return False


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Santo
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
class Santo(Base):
    __tablename__ = "Santos"

    id = Column("id_santo", Integer, primary_key=True)
    nome = Column("nome_santo", String, nullable=False, unique=True)
    nome_busca = Column("nome_busca_santo", String, index=True)
    foto_url = Column("foto_url_santo", String)
    biografia = Column("biografia_santo", Text)

    oracoes = relationship("Oracao", back_populates="santo", passive_deletes=True,
                           order_by="Oracao.titulo")
    novenas = relationship("Novena", back_populates="santo", passive_deletes=True,
                           order_by="Novena.titulo")
    livros = relationship("Livro", back_populates="santo", passive_deletes=True,
                          order_by="Livro.titulo")

    # sempre que o nome muda, atualiza a coluna nome_busca (sem acento)
    @validates("nome")
    def _atualizar_nome_busca(self, _chave, valor):
        self.nome_busca = _normalizar(valor) if valor else None
        return valor

    # lista os santos em ordem alfabética, paginado
    # (@classmethod: chamado direto pela classe, ex.: Santo.listar_todos_santos(session), sem precisar de um objeto)
    @classmethod
    def listar_todos_santos(cls, session, pagina: int = 1, limite: int = Limite_Maximo_Por_Pagina):
        return list(session.scalars(_paginar(select(cls).order_by(cls.nome), pagina, limite)))

    # busca por parte do nome, sem diferenciar acento ou maiúscula
    @classmethod
    def buscar_por_nome(cls, session, nome: str):
        nome_buscado = f"%{_normalizar(nome)}%"
        return list(session.scalars(select(cls).where(cls.nome_busca.like(nome_buscado)).order_by(cls.nome)))

    # devolve o santo pelo id (ou None)
    @classmethod
    def buscar_por_id(cls, session, id_santo: int):
        return session.get(cls, id_santo)

    # orações ligadas ao santo
    def ver_oracao_santo(self):
        return list(self.oracoes)

    # novenas ligadas ao santo
    def ver_novena_santo(self):
        return list(self.novenas)

    # livros ligados ao santo
    def ver_livro_santo(self):
        return list(self.livros)

    # cadastra um santo novo (precisa ter o token do adm)
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "nome")
        santo = cls(nome=dados["nome"], foto_url=dados.get("foto_url"),
                    biografia=dados.get("biografia"))
        _persistir(session, santo, f"um santo chamado '{dados['nome']}'")
        return santo

    # muda o nome, foto ou biografia de um santo
    @classmethod
    def atualizar(cls, session, id_santo: int, dados: dict, token: str):
        _exigir_autenticacao(token)
        _validar_alteracoes(dados, {"nome", "foto_url", "biografia"}, obrigatorios=("nome",))
        santo = _buscar_ou_erro(session, cls, id_santo, "Santo")
        for campo, valor in dados.items():
            setattr(santo, campo, valor)
        _persistir(session, santo, f"um santo chamado '{santo.nome}'")
        return santo

    # exclui o santo; orações, novenas e livros ficam sem santo com set null
    @classmethod
    def excluir(cls, session, id_santo: int, token: str) -> None:
        _exigir_autenticacao(token)
        santo = _buscar_ou_erro(session, cls, id_santo, "Santo")
        _remover(session, santo, f"o santo '{santo.nome}'")


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Momento do dia
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
class MomentoDia(Base):
    __tablename__ = "Momentos_Dia"

    id = Column("id_momento_dia", Integer, primary_key=True)
    bloco = Column("bloco_momento_dia", Enum(BlocoMomento), nullable=False, unique=True)

    oracoes = relationship("Oracao", secondary=Oracao_Momento_Dia, back_populates="momentos",
                           passive_deletes=True)

    # lista os momentos do dia (ao acordar, antes de dormir, essas coisas)
    @classmethod
    def listar_momentos_do_dia(cls, session):
        return list(session.scalars(select(cls).order_by(cls.id)))


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Oração
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
class Oracao(Base):
    __tablename__ = "Oracoes"
    __table_args__ = (
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
    santo_id = Column("id_santo", Integer, ForeignKey("Santos.id_santo", ondelete="SET NULL"))

    santo = relationship("Santo", back_populates="oracoes")
    momentos = relationship("MomentoDia", secondary=Oracao_Momento_Dia, back_populates="oracoes",
                            passive_deletes=True)
    dias_novena = relationship("Conteudo_Dia_Novena", secondary=Oracao_Dia_Novena, back_populates="oracoes",
                               passive_deletes=True)

    # lista todas as orações em ordem alfabética
    @classmethod
    def listar_todas_as_oracoes(cls, session, pagina: int = 1, limite: int = Limite_Maximo_Por_Pagina):
        return list(session.scalars(_paginar(select(cls).order_by(cls.titulo), pagina, limite)))

    # lista só as orações básicas (Pai Nosso, Ave Maria, etc)
    @classmethod
    def listar_oracoes_basicas(cls, session, pagina: int = 1, limite: int = Limite_Maximo_Por_Pagina):
        consulta = select(cls).where(cls.basica.is_(True)).order_by(cls.id)
        return list(session.scalars(_paginar(consulta, pagina, limite)))

    # orações de um momento do dia; aceita o objeto, o enum, o texto ou o id
    @classmethod
    def filtrar_por_momento_do_dia(cls, session, momento, pagina: int = 1,
                        limite: int = Limite_Maximo_Por_Pagina):
        consulta = select(cls).join(cls.momentos)
        if isinstance(momento, MomentoDia):
            consulta = consulta.where(MomentoDia.id == momento.id)
        elif isinstance(momento, (BlocoMomento, str)):
            consulta = consulta.where(MomentoDia.bloco == _converter_enum(BlocoMomento, momento, "momento"))
        else:
            consulta = consulta.where(MomentoDia.id == momento)
        return list(session.scalars(_paginar(consulta.order_by(cls.titulo), pagina, limite)))

    # orações de um santo
    @classmethod
    def buscar_por_santo(cls, session, santo_id: int):
        return list(session.scalars(select(cls).where(cls.santo_id == santo_id).order_by(cls.titulo)))

    # cadastra uma oração, já com os momentos do dia se vierem
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "titulo", "texto")
        santo_id = dados.get("santo_id")
        _validar_santo(session, santo_id)
        oracao = cls(titulo=dados["titulo"], texto=dados["texto"],
                     basica=bool(dados.get("basica", False)), santo_id=santo_id)
        if dados.get("momentos_ids"):
            oracao.categorizar_por_momento_do_dia(_resolver_momentos(session, dados["momentos_ids"]), token)
        escopo = "para este santo" if santo_id is not None else "entre as orações gerais"
        _persistir(session, oracao, f"uma oração '{dados['titulo']}' {escopo}")
        return oracao

    # altera os campos da oração e, se vierem, os momentos do dia
    @classmethod
    def atualizar(cls, session, id_oracao: int, dados: dict, token: str):
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
                oracao.categorizar_por_momento_do_dia(_resolver_momentos(session, dados["momentos_ids"]), token)
        escopo = "para este santo" if oracao.santo_id is not None else "entre as orações gerais"
        _persistir(session, oracao, f"uma oração '{oracao.titulo}' {escopo}")
        return oracao

    # exclui a oração
    @classmethod
    def excluir(cls, session, id_oracao: int, token: str) -> None:
        _exigir_autenticacao(token)
        oracao = _buscar_ou_erro(session, cls, id_oracao, "Oração")
        _remover(session, oracao, f"a oração '{oracao.titulo}'")

    # define em quais momentos do dia a oração aparece
    def categorizar_por_momento_do_dia(self, momentos, token: str) -> None:
        _exigir_autenticacao(token)
        itens = list(momentos or [])
        if all(isinstance(momento, MomentoDia) for momento in itens):
            self.momentos = itens
        else:
            self.momentos = _resolver_momentos(_sessao_de(self), itens)


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Novena e Conteudo_Dia_Novena
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
class Novena(Base):
    __tablename__ = "Novenas"
    __table_args__ = (
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
    dias = relationship("Conteudo_Dia_Novena", back_populates="novena", cascade="all, delete-orphan",
                        passive_deletes=True, order_by="Conteudo_Dia_Novena.numero_do_dia")
    agendas = relationship("Agenda", back_populates="novena", passive_deletes=True,
                           order_by="Agenda.data_inicio")

    # lista as novenas em ordem alfabética
    @classmethod
    def listar_todas_novenas(cls, session, pagina: int = 1, limite: int = Limite_Maximo_Por_Pagina):
        return list(session.scalars(_paginar(select(cls).order_by(cls.titulo), pagina, limite)))

    # devolve a novena pelo id (ou None)
    @classmethod
    def buscar_por_id(cls, session, id_novena: int):
        return session.get(cls, id_novena)

    # novenas de um santo
    @classmethod
    def buscar_por_santo(cls, session, santo_id: int):
        return list(session.scalars(select(cls).where(cls.santo_id == santo_id).order_by(cls.titulo)))

    # os 9 dias da novena
    def ver_dias_da_novena(self):
        return list(self.dias)

    # cadastra a novena junto com os 9 dias dela
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "titulo")
        dias = dados.get("dias") or []
        if len(dias) != Dias_Da_Novena:
            raise Erro_De_Dados_Incorretos(f"Uma novena precisa ter {Dias_Da_Novena} dias, conserta!")
        santo_id = dados.get("santo_id")
        _validar_santo(session, santo_id)

        novena = cls(titulo=dados["titulo"], descricao=dados.get("descricao"), santo_id=santo_id)
        with session.no_autoflush:
            for numero, dia in enumerate(dias, start=1):
                _exigir_campos(dia, "texto_reflexao")
                item = Conteudo_Dia_Novena(numero_do_dia=numero, texto_reflexao=dia["texto_reflexao"])
                item.oracoes = _buscar_oracoes(session, dia.get("oracoes_base_ids"))
                novena.dias.append(item)
        escopo = "para este santo" if santo_id is not None else "sem santo associado"
        _persistir(session, novena, f"uma novena '{dados['titulo']}' {escopo}")
        return novena

    # muda título, descrição ou santo da novena
    @classmethod
    def atualizar(cls, session, id_novena: int, dados: dict, token: str):
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

    # exclui a novena e os dias dela (bloqueia se ainda tiver agenda ativa)
    @classmethod
    def excluir(cls, session, id_novena: int, token: str) -> None:
        _exigir_autenticacao(token)
        novena = _buscar_ou_erro(session, cls, id_novena, "Novena")
        if Agenda.buscar_agenda_ativa_da_novena(session, novena.id) is not None:
            raise Erro_De_Dados_Incorretos(
                "Esta novena tem uma agenda ativa. Tem que cancelar a agenda antes de excluir a novena.")
        _remover(session, novena, f"a novena '{novena.titulo}'")


class Conteudo_Dia_Novena(Base):
    __tablename__ = "Dias_Novena"
    __table_args__ = (
        UniqueConstraint("id_novena", "numero_do_dia_da_novena", name="numero_do_dia_da_novena"),
        CheckConstraint("numero_do_dia_da_novena BETWEEN 1 AND 9", name="intervalo_do_dia_da_novena"),
    )

    id = Column("id_dia_novena", Integer, primary_key=True)
    novena_id = Column("id_novena", Integer, ForeignKey("Novenas.id_novena", ondelete="CASCADE"),
                       nullable=False)
    numero_do_dia = Column("numero_do_dia_da_novena", Integer, nullable=False)
    texto_reflexao = Column("texto_reflexao_dia_novena", Text, nullable=False)

    novena = relationship("Novena", back_populates="dias")
    oracoes = relationship("Oracao", secondary=Oracao_Dia_Novena, back_populates="dias_novena",
                           passive_deletes=True)

    # busca o dia N de uma novena
    @classmethod
    def buscar_dia_da_novena(cls, session, novena_id: int, dia: int):
        return session.scalar(
            select(cls).where(cls.novena_id == novena_id, cls.numero_do_dia == dia))

    # lista os dias de uma novena em ordem
    @classmethod
    def listar_dias_da_novena(cls, session, novena_id: int):
        return list(session.scalars(
            select(cls).where(cls.novena_id == novena_id).order_by(cls.numero_do_dia)))

    # orações rezadas no dia da novena
    def ver_oracoes_base(self):
        return list(self.oracoes)

    # altera a reflexão ou as orações de um dia
    @classmethod
    def atualizar(cls, session, id_dia_novena: int, dados: dict, token: str):
        _exigir_autenticacao(token)
        _validar_alteracoes(dados, {"texto_reflexao", "oracoes_base_ids"},
                            obrigatorios=("texto_reflexao",))
        dia = _buscar_ou_erro(session, cls, id_dia_novena, "Dia de novena")
        if "texto_reflexao" in dados:
            dia.texto_reflexao = dados["texto_reflexao"]
        if "oracoes_base_ids" in dados:
            dia.oracoes = _buscar_oracoes(session, dados["oracoes_base_ids"])
        _persistir(session, dia, f"o dia {dia.numero_do_dia} nesta novena")
        return dia


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Livro
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
class Livro(Base):
    __tablename__ = "Livros"
    __table_args__ = (UniqueConstraint("titulo_livro", "autor_livro", name="uq_livro_titulo_autor"),)

    id = Column("id_livro", Integer, primary_key=True)
    titulo = Column("titulo_livro", String, nullable=False)
    autor = Column("autor_livro", String, nullable=False)
    resumo = Column("resumo_livro", Text)
    contexto_historico = Column("contexto_historico_livro", Text)
    livro_recomendado = Column("recomendado_livro", Boolean, nullable=False, default=False)
    santo_id = Column("id_santo", Integer, ForeignKey("Santos.id_santo", ondelete="SET NULL"))

    santo = relationship("Santo", back_populates="livros")

    # lista os livros em ordem alfabética
    @classmethod
    def listar_todos_livros(cls, session, pagina: int = 1, limite: int = Limite_Maximo_Por_Pagina):
        return list(session.scalars(_paginar(select(cls).order_by(cls.titulo), pagina, limite)))

    # livros marcados como recomendados
    @classmethod
    def listar_livros_recomendados(cls, session, pagina: int = 1, limite: int = Limite_Maximo_Por_Pagina):
        consulta = select(cls).where(cls.livro_recomendado.is_(True)).order_by(cls.titulo)
        return list(session.scalars(_paginar(consulta, pagina, limite)))

    # devolve o livro pelo id
    @classmethod
    def buscar_por_id(cls, session, id_livro: int):
        return session.get(cls, id_livro)

    # livros de um santo
    @classmethod
    def buscar_por_santo(cls, session, santo_id: int):
        return list(session.scalars(select(cls).where(cls.santo_id == santo_id).order_by(cls.titulo)))

    # cadastra um livro
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

    # altera os dados de um livro
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

    # exclui um livro
    @classmethod
    def excluir(cls, session, id_livro: int, token: str) -> None:
        _exigir_autenticacao(token)
        livro = _buscar_ou_erro(session, cls, id_livro, "Livro")
        _remover(session, livro, f"o livro '{livro.titulo}'")


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Agenda
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
class Agenda(Base):
    __tablename__ = "Agendas"
    __table_args__ = (
        CheckConstraint("data_fim_agenda >= data_inicio_agenda", name="ck_agenda_periodo"),
        CheckConstraint("tipo_agenda = 'NOVENA' OR id_novena IS NULL",
                        name="ck_agenda_novena_so_no_tipo_novena"),
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

    # True se a data está entre hoje-7 e hoje+7
    @staticmethod
    def liturgia_dentro_do_intervalo(data: date, hoje: date | None = None) -> bool:
        hoje = hoje or date.today()
        return abs((data - hoje).days) <= Periodo_Disponivel_De_Liturgias

    # lança erro quando a data sai da janela da liturgia
    @classmethod
    def validar_intervalo_da_liturgia(cls, data: date) -> None:
        if not cls.liturgia_dentro_do_intervalo(data):
            raise Erro_Da_Liturgia_Fora_Da_Data_Permitida()

    # agenda a novena por 9 dias a partir da data (só pode ter uma agenda ativa)
    @classmethod
    def agendar_novena(cls, session, novena_id: int, data_inicio, token: str):
        _exigir_autenticacao(token)
        _buscar_ou_erro(session, Novena, novena_id, "Novena")
        inicio = _converter_data(data_inicio, "data_inicio")
        hoje = date.today()
        for anterior in session.scalars(select(cls).where(
                cls.novena_id == novena_id, cls.status == StatusAgenda.ATIVA)):
            if anterior.data_fim < hoje:
                anterior.status = StatusAgenda.CONCLUIDA
            else:
                raise Erro_De_Registros_Duplicados(
                    "Esta novena já tem uma agenda ativa. Cancele-a (cancelar) ou "
                    "reprograme-a (atualizar_progresso).")
        session.flush()
        agenda = cls(tipo=TipoAgenda.NOVENA, novena_id=novena_id, data_inicio=inicio,
                     data_fim=inicio + timedelta(days=Dias_Da_Novena - 1),
                     status=StatusAgenda.ATIVA)
        _persistir(session, agenda, "uma agenda ativa para esta novena")
        return agenda

    # reprograma a data de início (e de fim) de uma agenda ativa
    def atualizar_progresso(self, nova_data_inicio, token: str) -> None:
        _exigir_autenticacao(token)
        if self.tipo != TipoAgenda.NOVENA:
            raise Erro_De_Dados_Incorretos("Só agendas de novena têm progresso.")
        if self.status != StatusAgenda.ATIVA:
            raise Erro_De_Dados_Incorretos("Só agendas ativas podem ser atualizadas.")
        inicio = _converter_data(nova_data_inicio, "nova_data_inicio")
        self.data_inicio = inicio
        self.data_fim = inicio + timedelta(days=Dias_Da_Novena - 1)
        _persistir(_sessao_de(self), self, "uma agenda ativa para esta novena")

    # cancela a agenda (ela fica guardada como histórico)
    def cancelar(self, token: str) -> None:
        _exigir_autenticacao(token)
        if self.status != StatusAgenda.ATIVA:
            raise Erro_De_Dados_Incorretos("Só agendas ativas podem ser canceladas.")
        self.status = StatusAgenda.CANCELADA
        _persistir(_sessao_de(self), self, "esta agenda")

    # cria a agenda que reserva um período para a liturgia
    @classmethod
    def agendar_liturgias(cls, session, data_inicio, data_fim, token: str):
        _exigir_autenticacao(token)
        inicio = _converter_data(data_inicio, "data_inicio")
        fim = _converter_data(data_fim, "data_fim")
        if fim < inicio:
            raise Erro_De_Dados_Incorretos("A data final não pode ser anterior à data inicial.")
        agenda = cls(tipo=TipoAgenda.LITURGIA, data_inicio=inicio, data_fim=fim,
                     status=StatusAgenda.ATIVA)
        _persistir(session, agenda, "esta agenda de liturgia")
        return agenda

    # agenda ativa (em andamento ou futura) de uma novena
    @classmethod
    def buscar_agenda_ativa_da_novena(cls, session, novena_id: int, hoje: date | None = None):
        hoje = hoje or date.today()
        return session.scalar(
            select(cls).where(cls.novena_id == novena_id, cls.status == StatusAgenda.ATIVA,
                              cls.data_fim >= hoje)
            .order_by(cls.data_inicio, cls.id))

    # dia da novena hoje (1 a 9) (Coloca 0 se ainda não começou ou já acabou)
    def calcular_dia_atual(self, hoje: date | None = None) -> int:
        if self.tipo != TipoAgenda.NOVENA:
            raise Erro_De_Dados_Incorretos("Só agendas de novena têm dia atual.")
        if self.status != StatusAgenda.ATIVA:
            return 0
        hoje = hoje or date.today()
        dia = (hoje - self.data_inicio).days + 1
        return dia if 1 <= dia <= Dias_Da_Novena else 0

    # agendas ativas de um tipo (novena ou liturgia) que ainda não terminaram
    @classmethod
    def listar_agendas_ativas(cls, session, tipo, hoje: date | None = None):
        tipo = _converter_enum(TipoAgenda, tipo, "tipo")
        hoje = hoje or date.today()
        return list(session.scalars(
            select(cls).where(cls.tipo == tipo, cls.status == StatusAgenda.ATIVA,
                              cls.data_fim >= hoje)
            .order_by(cls.data_inicio, cls.id)))


# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# Liturgia: LiturgiaDia e LiturgiaHora
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ #
# a liturgia só pode ser cadastrada numa agenda de liturgia ativa que esteja dentro da data
def _validar_agenda_liturgia(session, agenda_id, data: date) -> None:
    agenda = session.get(Agenda, agenda_id) if agenda_id is not None else None
    if agenda is None:
        raise Erro_De_Dados_Incorretos(f"Agenda {agenda_id} não encontrada.")
    if agenda.tipo != TipoAgenda.LITURGIA:
        raise Erro_De_Dados_Incorretos("A agenda informada não é de liturgia.")
    if agenda.status != StatusAgenda.ATIVA:
        raise Erro_De_Dados_Incorretos("A agenda de liturgia informada não está ativa.")
    if not agenda.data_inicio <= data <= agenda.data_fim:
        raise Erro_De_Dados_Incorretos(
            f"A data {data.isoformat()} está fora do período da agenda "
            f"({agenda.data_inicio.isoformat()} a {agenda.data_fim.isoformat()}).")


# monta o SELECT da liturgia de uma data, ignorando agendas canceladas
def _consulta_liturgia_visivel(modelo, data: date):
    return (select(modelo).join(modelo.agenda)
            .where(modelo.data == data, Agenda.status != StatusAgenda.CANCELADA))


class LiturgiaDia(Base):
    __tablename__ = "Liturgia_Dia"

    id = Column("id_liturgia_dia", Integer, primary_key=True)
    agenda_id = Column("id_agenda", Integer, ForeignKey("Agendas.id_agenda"), nullable=False,
                       index=True)
    data = Column("data_liturgia_dia", Date, nullable=False, unique=True)
    santo_celebrado = Column("santo_celebrado_liturgia_dia", Text)
    primeira_leitura = Column("primeira_leitura_liturgia_dia", Text)
    salmo = Column("salmo_liturgia_dia", Text)
    evangelho = Column("evangelho_liturgia_dia", Text)
    segunda_leitura = Column("segunda_leitura_liturgia_dia", Text)

    agenda = relationship("Agenda", back_populates="liturgias_dia")

    Campos_Texto = ("santo_celebrado", "primeira_leitura", "salmo", "evangelho", "segunda_leitura")

    # Liturgia do Dia de uma data
    @classmethod
    def buscar_por_data(cls, session, data: date):
        Agenda.validar_intervalo_da_liturgia(data)
        return session.scalar(_consulta_liturgia_visivel(cls, data))

    # True quando o dia tem segunda leitura (domingos e solenidades)
    def tem_segunda_leitura_no_dia(self) -> bool:
        return bool(self.segunda_leitura and self.segunda_leitura.strip())

    # cadastra as leituras de uma data dentro de uma agenda de liturgia
    @classmethod
    def cadastrar(cls, session, dados: dict, token: str):
        _exigir_autenticacao(token)
        _exigir_campos(dados, "data", "agenda_id")
        dia = _converter_data(dados["data"])
        _validar_agenda_liturgia(session, dados["agenda_id"], dia)
        registro = cls(data=dia, agenda_id=dados["agenda_id"],
                       **{campo: dados.get(campo) for campo in cls.Campos_Texto})
        _persistir(session, registro, f"uma Liturgia do Dia em {dia.isoformat()}")
        return registro

    # altera as leituras ou a data/agenda de uma Liturgia do Dia
    @classmethod
    def atualizar(cls, session, id_liturgia_dia: int, dados: dict, token: str):
        _exigir_autenticacao(token)
        _validar_alteracoes(dados, {"data", "agenda_id", *cls.Campos_Texto},
                            obrigatorios=("data", "agenda_id"))
        registro = _buscar_ou_erro(session, cls, id_liturgia_dia, "Liturgia do Dia")
        nova_data = _converter_data(dados["data"]) if "data" in dados else registro.data
        nova_agenda = dados.get("agenda_id", registro.agenda_id)
        if "data" in dados or "agenda_id" in dados:
            _validar_agenda_liturgia(session, nova_agenda, nova_data)
        registro.data, registro.agenda_id = nova_data, nova_agenda
        for campo in cls.Campos_Texto:
            if campo in dados:
                setattr(registro, campo, dados[campo])
        _persistir(session, registro, f"uma Liturgia do Dia em {nova_data.isoformat()}")
        return registro

    # exclui a Liturgia do Dia
    @classmethod
    def excluir(cls, session, id_liturgia_dia: int, token: str) -> None:
        _exigir_autenticacao(token)
        registro = _buscar_ou_erro(session, cls, id_liturgia_dia, "Liturgia do Dia")
        _remover(session, registro, f"a Liturgia do Dia de {registro.data.isoformat()}")


class LiturgiaHora(Base):
    __tablename__ = "Liturgia_Hora"
    __table_args__ = (
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

    # organiza todos os blocos (laudes, horas médias, vésperas) de uma data
    @classmethod
    def buscar_por_data(cls, session, data: date):
        Agenda.validar_intervalo_da_liturgia(data)
        return list(session.scalars(_consulta_liturgia_visivel(cls, data).order_by(cls.id)))

    # um bloco específico de uma data
    @classmethod
    def buscar_por_bloco(cls, session, data: date, bloco):
        Agenda.validar_intervalo_da_liturgia(data)
        bloco = _converter_enum(BlocoLiturgia, bloco, "bloco")
        return session.scalar(_consulta_liturgia_visivel(cls, data).where(cls.bloco == bloco))

    # cadastra um bloco da Liturgia das Horas
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

    # altera texto, bloco, data ou agenda do registro
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

    # exclui o registro da Liturgia das Horas
    @classmethod
    def excluir(cls, session, id_liturgia_hora: int, token: str) -> None:
        _exigir_autenticacao(token)
        registro = _buscar_ou_erro(session, cls, id_liturgia_hora, "Liturgia das Horas")
        _remover(session, registro, f"o registro de {registro.bloco.value} de {registro.data.isoformat()}")

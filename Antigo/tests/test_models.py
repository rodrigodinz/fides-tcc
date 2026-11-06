from datetime import date, timedelta

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from database.connection import Base, criar_engine
from database.models import (
    Administrador, Agenda, AutenticacaoError, BlocoLiturgia, BlocoMomento, DadosInvalidosError,
    DiaNovena, ForaDoIntervaloError, Livro, LiturgiaDia, LiturgiaHora,
    MomentoDia, Novena, Oracao, RegistroDuplicadoError, RegistroNaoEncontradoError, Santo,
    StatusAgenda, TipoAgenda,
)
from database import seeds
from database.seeds import (EsquemaDesatualizadoError, executar_seeds, popular_banco,
                            resolver_credenciais_admin)
from sqlalchemy.orm import sessionmaker


VARS_ADMIN = ("FIDES_ADMIN_LOGIN", "FIDES_ADMIN_SENHA", "FIDES_ADMIN_PASSWORD", "FIDES_ADMIN_EMAIL")


@pytest.fixture(autouse=True)
def ambiente_limpo(monkeypatch):
    """Isola cada teste de variáveis de ambiente da máquina/CI."""
    for nome in VARS_ADMIN:
        monkeypatch.delenv(nome, raising=False)


def _banco(tmp_path=None):
    url = f"sqlite:///{tmp_path / 'teste.db'}" if tmp_path else "sqlite:///:memory:"
    engine = criar_engine(url)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def session():
    with sessionmaker(bind=_banco())() as s:
        executar_seeds(s)
        s.commit()
        yield s


@pytest.fixture()
def token(session):
    return Administrador.autenticar(session, "adm", "senha")


def _oracao(session, titulo, santo_id=None):
    return session.scalar(select(Oracao).where(Oracao.titulo == titulo, Oracao.santo_id == santo_id))


def _novena(session, titulo):
    return session.scalar(select(Novena).where(Novena.titulo == titulo))


def _total_liturgia(session):
    return (session.scalar(select(func.count()).select_from(LiturgiaDia))
            + session.scalar(select(func.count()).select_from(LiturgiaHora)))


def _agenda_liturgia(session):
    return session.scalar(select(Agenda).where(Agenda.tipo == TipoAgenda.LITURGIA))


def _dias(texto="dia"):
    return [{"texto_reflexao": f"{texto} {n}"} for n in range(1, 10)]


def test_busca_ignora_acentos(session):
    assert [s.nome for s in Santo.buscar_nome(session, "tomas")] == ["São Tomás de Aquino"]


def test_paginacao_respeita_limite_maximo(session):
    assert len(Santo.listar_todos(session, pagina=1, limite=2)) == 2
    assert len(Santo.listar_todos(session, pagina=1, limite=999)) <= 20


def test_santo_carrega_conteudos_vinculados(session):
    teresa = Santo.buscar_nome(session, "ávila")[0]
    assert [o.titulo for o in teresa.ver_oracao_santo()] == ["Nada te perturbe"]
    assert [l.titulo for l in teresa.ver_livro_santo()] == ["O Castelo Interior"]


def test_oracoes_basicas_e_filtro_por_momento(session):
    assert {o.titulo for o in Oracao.listar_basicas(session)} == {
        "Pai Nosso", "Ave Maria", "Glória ao Pai", "Credo", "Santo Anjo"}
    acordar = next(m for m in MomentoDia.listar_todos(session) if m.bloco == BlocoMomento.AO_ACORDAR)
    titulos = {o.titulo for o in Oracao.filtrar_momento(session, acordar.id)}
    assert "Oferecimento do dia" in titulos and "Credo" not in titulos


def test_novena_tem_nove_dias_ordenados_com_oracoes_base(session):
    novena = _novena(session, "Novena a Santa Teresinha")
    dias = novena.obter_dias()
    assert [d.numero_dia for d in dias] == list(range(1, 10))
    assert {o.titulo for o in dias[0].obter_oracao_base()} == {"Pai Nosso", "Ave Maria"}
    assert DiaNovena.buscar_novena_dia(session, novena.id, 3).numero_dia == 3


def test_dia_da_novena_nao_repete_e_fica_entre_1_e_9(session):
    novena = _novena(session, "Novena a Santa Teresinha")
    session.add(DiaNovena(novena_id=novena.id, numero_dia=10, texto_reflexao="x"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_cadastro_exige_token(session):
    with pytest.raises(AutenticacaoError):
        Santo.cadastrar(session, {"nome": "São Francisco de Assis"}, token="falso")


def test_autenticacao_invalida(session):
    with pytest.raises(AutenticacaoError):
        Administrador.autenticar(session, "adm", "errada")


def test_cadastros_com_token(session, token):
    santo = Santo.cadastrar(session, {"nome": "São Francisco de Assis"}, token)
    oracao = Oracao.cadastrar(session, {"titulo": "Oração da Paz", "texto": "...",
                                        "santo_id": santo.id, "momentos_ids": [1]}, token)
    assert oracao.momentos[0].bloco == BlocoMomento.AO_ACORDAR
    livro = Livro.cadastrar(session, {"titulo": "Fioretti", "autor": "Anônimo",
                                      "santo_id": santo.id}, token)
    assert livro.santo is santo


def test_novena_exige_exatamente_nove_dias(session, token):
    santo = Santo.buscar_nome(session, "agostinho")[0]
    with pytest.raises(DadosInvalidosError):
        Novena.cadastrar(session, {"titulo": "X", "santo_id": santo.id,
                                   "dias": [{"texto_reflexao": "a"}] * 8}, token)
    novena = Novena.cadastrar(session, {"titulo": "X", "santo_id": santo.id,
                                        "dias": [{"texto_reflexao": "a"}] * 9}, token)
    assert len(novena.dias) == 9


def test_liturgia_consultas_e_intervalo(session):
    """LiturgiaDia e LiturgiaHora são classes independentes (UML); a janela de
    ±7 dias (RNF07) é ``Agenda._dentro_intervalo``."""
    hoje = date.today()
    assert LiturgiaDia.buscar_data(session, hoje) is not None  # vem dos seeds
    assert LiturgiaHora.buscar_bloco(session, hoje, "laudes").bloco == BlocoLiturgia.LAUDES
    assert len(LiturgiaHora.buscar_data(session, hoje)) == 3
    with pytest.raises(ForaDoIntervaloError):
        LiturgiaDia.buscar_data(session, hoje + timedelta(days=8))
    with pytest.raises(ForaDoIntervaloError):
        LiturgiaHora.buscar_bloco(session, hoje - timedelta(days=8), "laudes")
    assert Agenda._dentro_intervalo(hoje - timedelta(days=7)) is True
    assert Agenda._dentro_intervalo(hoje + timedelta(days=8)) is False


def test_possui_segunda_leitura():
    assert LiturgiaDia(data=date.today(), segunda_leitura="  ").possui_segunda_leitura() is False
    assert LiturgiaDia(data=date.today()).possui_segunda_leitura() is False
    assert LiturgiaDia(data=date.today(), segunda_leitura="texto").possui_segunda_leitura() is True


def test_seeds_sao_idempotentes(session):
    executar_seeds(session)
    session.commit()
    assert len(Santo.listar_todos(session)) == 5
    assert len(Novena.listar_todas(session)) == 3
    assert len(MomentoDia.listar_todos(session)) == 4


def test_excluir_santo_preserva_conteudos_sem_vinculo(session, token):
    """UML: Santo — Oração/Novena/Livro é associação opcional (0..1), não composição.

    Mudança em relação à versão anterior, que apagava em cascata.
    """
    santo = Santo.buscar_nome(session, "agostinho")[0]
    ids = {"oracao": _oracao(session, "Tarde te amei", santo.id).id,
           "novena": _novena(session, "Novena a Santo Agostinho").id,
           "livro": session.scalar(select(Livro.id).where(Livro.titulo == "Confissões"))}
    Santo.excluir(session, santo.id, token)
    session.commit()
    session.expire_all()
    assert Santo.buscar_id(session, santo.id) is None
    assert session.get(Oracao, ids["oracao"]).santo_id is None
    assert session.get(Novena, ids["novena"]).santo_id is None
    assert len(session.get(Novena, ids["novena"]).dias) == 9
    assert session.get(Livro, ids["livro"]).santo_id is None
    assert len(Oracao.listar_basicas(session)) == 5


# =========================================================================== #
# Conteúdo inicial: santos, livros
# =========================================================================== #
def test_cinco_santos_esperados_sem_duplicar_teresa(session):
    nomes = {s.nome for s in Santo.listar_todos(session)}
    assert nomes == {"São Tomás de Aquino", "Santa Teresinha do Menino Jesus",
                     "Santa Teresa d'Ávila", "Santo Agostinho", "São Josemaria Escrivá"}
    assert [s.nome for s in Santo.buscar_nome(session, "avila")] == ["Santa Teresa d'Ávila"]


def test_oito_livros_com_autores_e_santos_corretos(session):
    livros = {l.titulo: l for l in Livro.listar_todos(session)}
    assert len(livros) == 8
    esperado = {
        "Teologia do Corpo": ("São João Paulo II", None),
        "O Castelo Interior": ("Santa Teresa de Jesus", "Santa Teresa d'Ávila"),
        "Caminho": ("São Josemaria Escrivá", "São Josemaria Escrivá"),
        "Suma Teológica": ("São Tomás de Aquino", "São Tomás de Aquino"),
        "Confissões": ("Santo Agostinho", "Santo Agostinho"),
        "Todos os Caminhos Levam a Roma": ("Scott Hahn", None),
        "História de uma Alma": ("Santa Teresinha do Menino Jesus", "Santa Teresinha do Menino Jesus"),
        "O Cristão Bem Formado": ("São João Bosco", None),
    }
    assert set(livros) == set(esperado)
    for titulo, (autor, santo) in esperado.items():
        assert livros[titulo].autor == autor
        assert (livros[titulo].santo.nome if livros[titulo].santo else None) == santo
    assert livros["Confissões"].autor != "São Tomás de Aquino"


# =========================================================================== #
# Orações
# =========================================================================== #
def test_classificacao_basica_e_complementar(session):
    gerais = {o.titulo: o.basica for o in session.scalars(select(Oracao).where(Oracao.santo_id.is_(None)))}
    assert gerais == {
        "Pai Nosso": True, "Ave Maria": True, "Glória ao Pai": True, "Credo": True,
        "Santo Anjo": True,
        "Invocação do Espírito Santo": False, "Oração a São Miguel Arcanjo": False,
        "Oferecimento do dia": False, "Bênção da refeição": False, "Alma de Cristo": False,
    }


def test_sao_miguel_comeca_como_exigido(session):
    texto = _oracao(session, "Oração a São Miguel Arcanjo").texto
    assert texto.startswith("São Miguel Arcanjo, defendei-nos no combate")


def test_invocacao_preservada_e_complementar(session):
    inv = _oracao(session, "Invocação do Espírito Santo")
    assert inv.texto.startswith("Vinde, Espírito Santo, enchei os corações dos vossos fiéis")
    assert inv.basica is False
    assert {m.bloco for m in inv.momentos} == {BlocoMomento.AO_ACORDAR}


def test_oracoes_de_santos_e_momentos_preservadas(session):
    teresa = Santo.buscar_nome(session, "avila")[0]
    agostinho = Santo.buscar_nome(session, "agostinho")[0]
    assert [o.titulo for o in teresa.ver_oracao_santo()] == ["Nada te perturbe"]
    assert [o.titulo for o in agostinho.ver_oracao_santo()] == ["Tarde te amei"]
    assert {m.bloco for m in _oracao(session, "Santo Anjo").momentos} == {BlocoMomento.ANTES_DE_DORMIR}
    assert {m.bloco for m in _oracao(session, "Bênção da refeição").momentos} == {BlocoMomento.REFEICOES}
    assert {m.bloco for m in _oracao(session, "Alma de Cristo").momentos} == {BlocoMomento.MISSA}
    assert {m.bloco for m in _oracao(session, "Oferecimento do dia").momentos} == {BlocoMomento.AO_ACORDAR}


def test_filtro_por_momento_ante_de_dormir(session):
    dormir = next(m for m in MomentoDia.listar_todos(session) if m.bloco == BlocoMomento.ANTES_DE_DORMIR)
    assert {o.titulo for o in Oracao.filtrar_momento(session, dormir.id)} == {
        "Pai Nosso", "Ave Maria", "Santo Anjo"}


def test_sem_oracoes_duplicadas_por_titulo(session):
    executar_seeds(session)
    session.commit()
    repetidos = session.execute(
        select(Oracao.titulo, Oracao.santo_id, func.count()).group_by(Oracao.titulo, Oracao.santo_id)
        .having(func.count() > 1)).all()
    assert repetidos == []
    assert session.scalar(select(func.count()).select_from(Oracao)) == 12


# =========================================================================== #
# Novenas e momentos
# =========================================================================== #
TITULOS_NOVENAS = {
    "Novena a Santa Teresinha": "Santa Teresinha do Menino Jesus",
    "Novena a Santa Teresa d'Ávila": "Santa Teresa d'Ávila",
    "Novena a Santo Agostinho": "Santo Agostinho",
}


def test_tres_novenas_com_nove_dias_e_textos_proprios(session):
    novenas = Novena.listar_todas(session)
    assert {n.titulo: n.santo.nome for n in novenas} == TITULOS_NOVENAS
    for n in novenas:
        dias = n.obter_dias()
        assert [d.numero_dia for d in dias] == list(range(1, 10))
        assert len({d.texto_reflexao for d in dias}) == 9
        assert all(d.texto_reflexao.startswith(f"Dia {d.numero_dia} –") for d in dias)


def test_novenas_associam_oracoes_base(session):
    teresinha = _novena(session, "Novena a Santa Teresinha")
    assert {o.titulo for o in teresinha.dias[0].obter_oracao_base()} == {"Pai Nosso", "Ave Maria"}
    for titulo, extra in (("Novena a Santa Teresa d'Ávila", "Nada te perturbe"),
                          ("Novena a Santo Agostinho", "Tarde te amei")):
        novena = _novena(session, titulo)
        assert {o.titulo for o in novena.dias[0].obter_oracao_base()} == {"Pai Nosso", "Ave Maria", "Glória ao Pai"}
        assert extra in {o.titulo for o in novena.dias[8].obter_oracao_base()}


def test_novena_de_teresinha_preserva_conteudo_original(session):
    novena = _novena(session, "Novena a Santa Teresinha")
    assert novena.descricao.startswith("Nove dias de reflexão inspirados no 'pequeno caminho'")
    assert novena.dias[0].texto_reflexao.startswith("Dia 1 – Confiança. Teresinha aprendeu")
    assert novena.dias[8].texto_reflexao.startswith("Dia 9 – Gratidão.")


def test_novena_sem_nove_dias_e_rejeitada(session, token):
    santo = Santo.buscar_nome(session, "agostinho")[0]
    with pytest.raises(DadosInvalidosError):
        Novena.cadastrar(session, {"titulo": "Y", "santo_id": santo.id,
                                   "dias": [{"texto_reflexao": "a"}] * 10}, token)


def test_momentos_do_dia_inalterados(session):
    momentos = MomentoDia.listar_todos(session)
    assert [m.bloco for m in momentos] == [BlocoMomento.AO_ACORDAR, BlocoMomento.REFEICOES,
                                           BlocoMomento.MISSA, BlocoMomento.ANTES_DE_DORMIR]
    assert [m.bloco.value for m in momentos] == ["Ao acordar", "Refeições", "Missa", "Antes de dormir"]


# =========================================================================== #
# Administrador
# =========================================================================== #
def test_admin_padrao_criado_uma_vez_e_login_adm_senha(session):
    executar_seeds(session)
    session.commit()
    admins = session.scalars(select(Administrador)).all()
    assert [a.login for a in admins] == ["adm"]
    assert Administrador._validar_token(Administrador.autenticar(session, "adm", "senha"))


def test_senha_armazenada_como_hash(session):
    admin = session.scalar(select(Administrador))
    assert admin.senha_hash != "senha"
    assert "senha" not in admin.senha_hash.split("$")
    assert admin.senha_hash.startswith("pbkdf2_sha256$")


def test_senha_incorreta_e_login_inexistente_rejeitados(session):
    with pytest.raises(AutenticacaoError):
        Administrador.autenticar(session, "adm", "Senha")
    with pytest.raises(AutenticacaoError):
        Administrador.autenticar(session, "outro", "senha")
    with pytest.raises(AutenticacaoError) as erro:
        Administrador.autenticar(session, "adm", "errada-xyz")
    assert "errada-xyz" not in str(erro.value)


def test_login_e_senha_personalizados(monkeypatch):
    monkeypatch.setenv("FIDES_ADMIN_LOGIN", "padre")
    monkeypatch.setenv("FIDES_ADMIN_SENHA", "outra-senha")
    with sessionmaker(bind=_banco())() as s:
        executar_seeds(s)
        assert Administrador.autenticar(s, "padre", "outra-senha")
        with pytest.raises(AutenticacaoError):
            Administrador.autenticar(s, "adm", "senha")


def test_precedencia_senha_sobre_alias(monkeypatch):
    monkeypatch.setenv("FIDES_ADMIN_PASSWORD", "alias")
    assert resolver_credenciais_admin()[1] == "alias"  # só o alias definido
    monkeypatch.setenv("FIDES_ADMIN_SENHA", "principal")
    with pytest.warns(UserWarning, match="precedência"):
        assert resolver_credenciais_admin()[1] == "principal"
    monkeypatch.setenv("FIDES_ADMIN_PASSWORD", "principal")  # iguais: sem aviso
    assert resolver_credenciais_admin()[1] == "principal"


def test_padroes_de_desenvolvimento_sem_ambiente():
    assert resolver_credenciais_admin() == ("adm", "senha", None)


def test_email_opcional_tambem_autentica(monkeypatch):
    monkeypatch.setenv("FIDES_ADMIN_EMAIL", "admin@exemplo.com")
    with sessionmaker(bind=_banco())() as s:
        executar_seeds(s)
        assert Administrador.autenticar(s, "admin@exemplo.com", "senha")
        assert Administrador.autenticar(s, "adm", "senha")


def test_token_adulterado_expirado_e_ausente_rejeitados(session, monkeypatch):
    token = Administrador.autenticar(session, "adm", "senha")
    corpo, assinatura = token.split(".")
    assert not Administrador._validar_token(f"{corpo}.{'0' * len(assinatura)}")
    assert not Administrador._validar_token(None)
    assert not Administrador._validar_token("lixo")
    from database import models
    monkeypatch.setattr(models.time, "time", lambda: 9_999_999_999)
    assert not Administrador._validar_token(token)


def test_metodos_administrativos_exigem_token(session):
    santo = Santo.buscar_nome(session, "agostinho")[0]
    with pytest.raises(AutenticacaoError):
        Oracao.cadastrar(session, {"titulo": "X", "texto": "y"}, token="falso")
    with pytest.raises(AutenticacaoError):
        Livro.cadastrar(session, {"titulo": "X", "autor": "y"}, token=None)
    with pytest.raises(AutenticacaoError):
        Novena.cadastrar(session, {"titulo": "X", "santo_id": santo.id, "dias": []}, token="")
    with pytest.raises(AutenticacaoError):
        _oracao(session, "Pai Nosso").categorizar([], token="falso")


def test_token_nao_contem_senha(session):
    token = Administrador.autenticar(session, "adm", "senha")
    corpo = token.split(".")[0]
    import base64
    assert "senha" not in base64.urlsafe_b64decode(corpo.encode()).decode()


def test_banco_da_versao_anterior_e_recusado_sem_alterar_nada(tmp_path):
    """Arquivo criado antes da remodelagem UML: os seeds não misturam esquemas."""
    engine = _banco(tmp_path)
    with engine.begin() as con:  # simula a tabela da herança antiga
        con.execute(text('CREATE TABLE "Liturgia" (id_liturgia INTEGER PRIMARY KEY, '
                         'data_liturgia DATE NOT NULL, tipo_liturgia VARCHAR(10) NOT NULL)'))
    with sessionmaker(bind=engine)() as s:
        with pytest.raises(EsquemaDesatualizadoError, match="versão anterior"):
            popular_banco(s)
        assert s.scalar(select(func.count()).select_from(Santo)) == 0


def test_verificar_esquema_detecta_colunas_antigas(tmp_path):
    engine = _banco(tmp_path)
    with engine.begin() as con:
        con.execute(text('DROP TABLE "Livros"'))
        con.execute(text('CREATE TABLE "Livros" (id_livro INTEGER PRIMARY KEY, '
                         'titulo_livro VARCHAR NOT NULL, autor_livro VARCHAR NOT NULL)'))
    with engine.connect() as con:
        with pytest.raises(EsquemaDesatualizadoError, match="recomendado_livro"):
            seeds.verificar_esquema(con)


def test_reset_apaga_tambem_tabelas_antigas(tmp_path):
    from database.connection import apagar_tabelas
    engine = _banco(tmp_path)
    with engine.begin() as con:
        con.execute(text('CREATE TABLE "Liturgia" (id_liturgia INTEGER PRIMARY KEY)'))
    apagar_tabelas(engine)
    from sqlalchemy import inspect
    assert inspect(engine).get_table_names() == []


# =========================================================================== #
# Seeds: idempotência e transação
# =========================================================================== #
def test_seeds_repetidos_nao_duplicam_nada(session):
    def contagens():
        return [session.scalar(select(func.count()).select_from(m))
                for m in (Santo, Livro, Oracao, MomentoDia, Novena, DiaNovena, Administrador,
                          Agenda, LiturgiaDia, LiturgiaHora)]
    antes = contagens()
    popular_banco(session)
    popular_banco(session)
    assert contagens() == antes == [5, 8, 12, 4, 3, 27, 1, 4, 15, 45]


def test_seed_nao_sobrescreve_alteracao_do_administrador(session):
    santo = Santo.buscar_nome(session, "tomas")[0]
    santo.biografia = "editada no painel"
    popular_banco(session)
    assert santo.biografia == "editada no painel"


def test_falha_no_seed_faz_rollback_total(monkeypatch):
    def explode(*_a, **_k):
        raise RuntimeError("falha simulada")
    monkeypatch.setattr(seeds, "seed_livros", explode)
    with sessionmaker(bind=_banco())() as s:
        with pytest.raises(RuntimeError):
            popular_banco(s)
        assert s.scalar(select(func.count()).select_from(Santo)) == 0
        assert s.scalar(select(func.count()).select_from(Administrador)) == 0


# =========================================================================== #
# Liturgia de demonstração (seeds)
# =========================================================================== #
def test_liturgia_semeada_para_toda_a_janela(session):
    hoje = date.today()
    for deslocamento in range(-7, 8):
        dia = hoje + timedelta(days=deslocamento)
        registro = LiturgiaDia.buscar_data(session, dia)
        assert registro is not None
        assert registro.primeira_leitura and registro.salmo and registro.evangelho
        assert [h.bloco for h in sorted(LiturgiaHora.buscar_data(session, dia), key=lambda h: h.id)] == [
            BlocoLiturgia.LAUDES, BlocoLiturgia.HORAS_MEDIAS, BlocoLiturgia.VESPERAS]
        assert registro.possui_segunda_leitura() == (dia.weekday() == 6)  # só aos domingos
    assert _total_liturgia(session) == 15 * 4


def test_liturgia_fora_da_janela_nao_e_semeada(session):
    fora = date.today() + timedelta(days=8)
    assert session.scalar(select(func.count()).select_from(LiturgiaDia).where(LiturgiaDia.data == fora)) == 0
    assert session.scalar(select(func.count()).select_from(LiturgiaHora).where(LiturgiaHora.data == fora)) == 0


def test_seed_de_liturgia_e_idempotente_e_aceita_data_de_referencia(session):
    antes = _total_liturgia(session)
    popular_banco(session)
    assert _total_liturgia(session) == antes
    popular_banco(session, data_referencia=date(2030, 1, 15))
    popular_banco(session, data_referencia=date(2030, 1, 15))
    assert _total_liturgia(session) == antes + 60


def test_liturgia_do_dia_duplicada_e_rejeitada_pelo_banco(session):
    agenda = _agenda_liturgia(session)
    session.add(LiturgiaDia(data=date.today(), primeira_leitura="x", agenda_id=agenda.id))
    with pytest.raises(IntegrityError, match="UNIQUE"):
        session.flush()
    session.rollback()


# =========================================================================== #
# Unicidade de títulos (banco + erro de domínio)
# =========================================================================== #
def test_livro_duplicado_titulo_e_autor_rejeitado(session, token):
    with pytest.raises(RegistroDuplicadoError):
        Livro.cadastrar(session, {"titulo": "Caminho", "autor": "São Josemaria Escrivá"}, token)
    session.rollback()


def test_livro_mesmo_titulo_com_autor_diferente_e_permitido(session, token):
    livro = Livro.cadastrar(session, {"titulo": "Caminho", "autor": "Outro Autor"}, token)
    assert livro.id is not None


def test_novena_duplicada_para_o_mesmo_santo_rejeitada(session, token):
    santo = Santo.buscar_nome(session, "agostinho")[0]
    dias = [{"texto_reflexao": f"dia {n}"} for n in range(1, 10)]
    with pytest.raises(RegistroDuplicadoError):
        Novena.cadastrar(session, {"titulo": "Novena a Santo Agostinho", "santo_id": santo.id,
                                   "dias": dias}, token)
    session.rollback()


def test_novena_mesmo_titulo_para_outro_santo_e_permitida(session, token):
    tomas = Santo.buscar_nome(session, "tomas")[0]
    dias = [{"texto_reflexao": f"dia {n}"} for n in range(1, 10)]
    novena = Novena.cadastrar(session, {"titulo": "Novena a Santo Agostinho", "santo_id": tomas.id,
                                        "dias": dias}, token)
    assert novena.id is not None


def test_oracao_geral_duplicada_rejeitada(session, token):
    with pytest.raises(RegistroDuplicadoError):
        Oracao.cadastrar(session, {"titulo": "Pai Nosso", "texto": "outro texto"}, token)
    session.rollback()


def test_oracao_de_santo_duplicada_rejeitada_mas_outro_santo_pode_repetir_titulo(session, token):
    teresa = Santo.buscar_nome(session, "avila")[0]
    tomas = Santo.buscar_nome(session, "tomas")[0]
    with pytest.raises(RegistroDuplicadoError):
        Oracao.cadastrar(session, {"titulo": "Nada te perturbe", "texto": "x", "santo_id": teresa.id}, token)
    session.rollback()
    # mesmo título em outro santo, e igual a uma oração geral, são permitidos
    assert Oracao.cadastrar(session, {"titulo": "Nada te perturbe", "texto": "x", "santo_id": tomas.id}, token).id
    assert Oracao.cadastrar(session, {"titulo": "Nada te perturbe", "texto": "x"}, token).id


def test_santo_duplicado_gera_erro_de_dominio(session, token):
    with pytest.raises(RegistroDuplicadoError):
        Santo.cadastrar(session, {"nome": "Santo Agostinho"}, token)
    session.rollback()


def test_unicidade_vale_no_banco_mesmo_sem_passar_pelos_metodos(session):
    """O banco rejeita duplicatas inseridas diretamente pelo ORM/SQL."""
    session.add(Livro(titulo="Caminho", autor="São Josemaria Escrivá"))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()
    session.add(Oracao(titulo="Credo", texto="x", basica=False))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


# =========================================================================== #
# Remodelagem UML (30/10/2026): nomes de métodos
# =========================================================================== #
def test_metodos_renomeados_conforme_uml(session):
    teresa = Santo.buscar_nome(session, "avila")[0]
    assert [n.titulo for n in teresa.ver_novena_santo()] == ["Novena a Santa Teresa d'Ávila"]
    assert [l.titulo for l in teresa.ver_livro_santo()] == ["O Castelo Interior"]
    assert [o.titulo for o in teresa.ver_oracao_santo()] == ["Nada te perturbe"]
    dia = DiaNovena.buscar_novena_dia(session, _novena(session, "Novena a Santa Teresinha").id, 1)
    assert {o.titulo for o in dia.obter_oracao_base()} == {"Pai Nosso", "Ave Maria"}
    for antigo in ("obter_oracoes", "obter_novena", "obter_livro"):
        assert not hasattr(Santo, antigo)
    assert not hasattr(DiaNovena, "oracoes_base")


# =========================================================================== #
# Santo.atualizar / Santo.excluir
# =========================================================================== #
def test_santo_atualizar_altera_so_os_campos_informados(session, token):
    tomas = Santo.buscar_nome(session, "tomas")[0]
    foto = tomas.foto_url
    Santo.atualizar(session, tomas.id, {"nome": "Santo Tomás de Aquino", "biografia": "nova"}, token)
    session.commit()
    santo = Santo.buscar_id(session, tomas.id)
    assert (santo.nome, santo.biografia, santo.foto_url) == ("Santo Tomás de Aquino", "nova", foto)
    assert [s.id for s in Santo.buscar_nome(session, "santo tomas")] == [tomas.id]  # nome_busca acompanha


def test_santo_atualizar_valida_dados(session, token):
    tomas = Santo.buscar_nome(session, "tomas")[0]
    with pytest.raises(RegistroDuplicadoError):
        Santo.atualizar(session, tomas.id, {"nome": "Santo Agostinho"}, token)
    session.rollback()
    with pytest.raises(DadosInvalidosError, match="vazios"):
        Santo.atualizar(session, tomas.id, {"nome": ""}, token)
    with pytest.raises(DadosInvalidosError, match="desconhecidos"):
        Santo.atualizar(session, tomas.id, {"id": 99}, token)
    with pytest.raises(DadosInvalidosError, match="ao menos um campo"):
        Santo.atualizar(session, tomas.id, {}, token)
    with pytest.raises(RegistroNaoEncontradoError):
        Santo.atualizar(session, 9999, {"biografia": "x"}, token)


def test_excluir_santo_com_titulo_que_colidiria_e_recusado(session, token):
    Oracao.cadastrar(session, {"titulo": "Tarde te amei", "texto": "versão geral"}, token)
    agostinho = Santo.buscar_nome(session, "agostinho")[0]
    with pytest.raises(RegistroDuplicadoError, match="título repetido"):
        Santo.excluir(session, agostinho.id, token)
    session.rollback()


def test_exclusao_de_santo_por_sql_tambem_desvincula(session):
    """ON DELETE SET NULL no próprio banco (vale mesmo fora do ORM)."""
    assert session.execute(text("PRAGMA foreign_keys")).scalar() == 1
    tomas = Santo.buscar_nome(session, "tomas")[0]
    livro_id = session.scalar(select(Livro.id).where(Livro.titulo == "Suma Teológica"))
    session.execute(text('DELETE FROM "Santos" WHERE id_santo = :i'), {"i": tomas.id})
    session.commit()
    session.expire_all()
    assert session.get(Livro, livro_id).santo_id is None


# =========================================================================== #
# CRUD das demais classes (modelo; rotas de escrita são da Fase 2)
# =========================================================================== #
METODOS_PROTEGIDOS = [
    lambda s: Santo.atualizar(s, 1, {"biografia": "x"}, "falso"),
    lambda s: Santo.excluir(s, 1, "falso"),
    lambda s: Oracao.atualizar(s, 1, {"texto": "x"}, "falso"),
    lambda s: Oracao.excluir(s, 1, "falso"),
    lambda s: Novena.atualizar(s, 1, {"descricao": "x"}, "falso"),
    lambda s: Novena.excluir(s, 1, "falso"),
    lambda s: DiaNovena.atualizar(s, 1, {"texto_reflexao": "x"}, "falso"),
    lambda s: Livro.atualizar(s, 1, {"resumo": "x"}, "falso"),
    lambda s: Livro.excluir(s, 1, "falso"),
    lambda s: LiturgiaDia.cadastrar(s, {"data": date.today(), "agenda_id": 4}, "falso"),
    lambda s: LiturgiaDia.atualizar(s, 1, {"salmo": "x"}, "falso"),
    lambda s: LiturgiaDia.excluir(s, 1, "falso"),
    lambda s: LiturgiaHora.cadastrar(s, {"data": date.today(), "agenda_id": 4, "bloco": "laudes",
                                         "texto": "x"}, "falso"),
    lambda s: LiturgiaHora.atualizar(s, 1, {"texto": "x"}, "falso"),
    lambda s: LiturgiaHora.excluir(s, 1, "falso"),
    lambda s: Agenda.agendar_novena(s, 1, date.today(), "falso"),
    lambda s: Agenda.agendar_liturgias(s, date.today(), date.today(), "falso"),
    lambda s: s.get(Agenda, 1).atualizar_progresso(date.today(), "falso"),
    lambda s: s.get(Agenda, 1).cancelar("falso"),
]


@pytest.mark.parametrize("operacao", METODOS_PROTEGIDOS)
def test_metodos_de_escrita_novos_exigem_token(session, operacao):
    with pytest.raises(AutenticacaoError):
        operacao(session)


def test_oracao_atualizar_e_excluir(session, token):
    credo = _oracao(session, "Credo")
    Oracao.atualizar(session, credo.id, {"basica": False, "momentos_ids": ["ao_acordar", "missa"]}, token)
    assert credo.basica is False
    assert {m.bloco for m in credo.momentos} == {BlocoMomento.AO_ACORDAR, BlocoMomento.MISSA}
    with pytest.raises(RegistroDuplicadoError):
        Oracao.atualizar(session, credo.id, {"titulo": "Pai Nosso"}, token)
    session.rollback()

    pai_nosso = _oracao(session, "Pai Nosso")
    dia1 = DiaNovena.buscar_novena_dia(session, _novena(session, "Novena a Santa Teresinha").id, 1)
    Oracao.excluir(session, pai_nosso.id, token)
    session.commit()
    session.expire_all()
    assert _oracao(session, "Pai Nosso") is None
    assert {o.titulo for o in dia1.obter_oracao_base()} == {"Ave Maria"}  # vínculo removido


def test_novena_atualizar_e_excluir_remove_os_dias(session, token):
    agostinho = _novena(session, "Novena a Santo Agostinho")
    Novena.atualizar(session, agostinho.id, {"descricao": "nova descrição"}, token)
    assert agostinho.descricao == "nova descrição"
    with pytest.raises(DadosInvalidosError, match="agenda ativa"):
        Novena.excluir(session, agostinho.id, token)
    Agenda.buscar_ativa(session, agostinho.id).cancelar(token)
    Novena.excluir(session, agostinho.id, token)
    session.commit()
    assert _novena(session, "Novena a Santo Agostinho") is None
    assert DiaNovena.listar_novena(session, agostinho.id) == []
    historico = session.scalar(select(Agenda).where(Agenda.status == StatusAgenda.CANCELADA))
    assert historico is not None and historico.novena_id is None  # agenda fica como histórico


def test_dia_novena_atualizar_mantem_a_composicao(session, token):
    dia = DiaNovena.buscar_novena_dia(session, _novena(session, "Novena a Santa Teresinha").id, 2)
    credo = _oracao(session, "Credo")
    DiaNovena.atualizar(session, dia.id, {"texto_reflexao": "Novo texto", "oracoes_base_ids": [credo.id]},
                        token)
    assert dia.texto_reflexao == "Novo texto" and dia.obter_oracao_base() == [credo]
    with pytest.raises(DadosInvalidosError, match="desconhecidos"):
        DiaNovena.atualizar(session, dia.id, {"numero_dia": 3}, token)
    with pytest.raises(DadosInvalidosError, match="não encontradas"):
        DiaNovena.atualizar(session, dia.id, {"oracoes_base_ids": [9999]}, token)
    # dias nascem e morrem com a novena (composição 1 — 9): sem cadastrar/excluir isolados
    assert not hasattr(DiaNovena, "cadastrar") and not hasattr(DiaNovena, "excluir")


def test_livro_atualizar_e_excluir(session, token):
    livro = session.scalar(select(Livro).where(Livro.titulo == "Confissões"))
    Livro.atualizar(session, livro.id, {"livro_recomendado": True, "santo_id": None}, token)
    assert livro.livro_recomendado is True and livro.santo_id is None
    with pytest.raises(DadosInvalidosError, match="Santo 9999"):
        Livro.atualizar(session, livro.id, {"santo_id": 9999}, token)
    Livro.excluir(session, livro.id, token)
    session.commit()
    assert Livro.buscar_id(session, livro.id) is None
    with pytest.raises(RegistroNaoEncontradoError):
        Livro.excluir(session, livro.id, token)


# =========================================================================== #
# Livro recomendado (UC13 / US12)
# =========================================================================== #
def test_livros_recomendados_dos_seeds(session):
    assert [l.titulo for l in Livro.listar_recomendados(session)] == ["Caminho", "O Castelo Interior"]
    assert session.scalar(select(func.count()).select_from(Livro)
                          .where(Livro.livro_recomendado.is_(False))) == 6


def test_cadastrar_livro_recomendado(session, token):
    livro = Livro.cadastrar(session, {"titulo": "Filoteia", "autor": "São Francisco de Sales",
                                      "livro_recomendado": True}, token)
    assert livro in Livro.listar_recomendados(session)
    assert Livro.cadastrar(session, {"titulo": "X", "autor": "Y"}, token).livro_recomendado is False


# =========================================================================== #
# Novena com santo opcional (UML 0..1)
# =========================================================================== #
def test_novena_sem_santo_e_unicidade(session, token):
    geral = Novena.cadastrar(session, {"titulo": "Novena ao Espírito Santo", "dias": _dias()}, token)
    assert geral.santo is None and len(geral.dias) == 9
    with pytest.raises(RegistroDuplicadoError, match="sem santo"):
        Novena.cadastrar(session, {"titulo": "Novena ao Espírito Santo", "dias": _dias()}, token)
    session.rollback()
    # mesmo título é permitido quando um é de santo e o outro não
    teresinha = Santo.buscar_nome(session, "teresinha")[0]
    assert Novena.cadastrar(session, {"titulo": "Novena a Santa Teresinha", "dias": _dias()}, token).id
    assert teresinha.id is not None


# =========================================================================== #
# Agenda (UC05, UC06, UC07, UC08, UC10, UC14)
# =========================================================================== #
def test_seeds_criam_agendas_de_demonstracao(session):
    hoje = date.today()
    esperado = {"Novena a Santa Teresinha": (hoje - timedelta(days=4), 5),
                "Novena a Santa Teresa d'Ávila": (hoje, 1),
                "Novena a Santo Agostinho": (hoje + timedelta(days=2), 0)}
    for titulo, (inicio, dia_atual) in esperado.items():
        agenda = Agenda.buscar_ativa(session, _novena(session, titulo).id)
        assert (agenda.data_inicio, agenda.data_fim) == (inicio, inicio + timedelta(days=8))
        assert agenda.calcular_dia_atual() == dia_atual
    assert len(Agenda.listar_ativas(session, TipoAgenda.NOVENA)) == 3
    liturgia = Agenda.listar_ativas(session, "liturgia")
    assert [(a.data_inicio, a.data_fim) for a in liturgia] == [(hoje - timedelta(days=7),
                                                                hoje + timedelta(days=7))]


def test_calcular_dia_atual_nos_limites(session, token):
    novena = Novena.cadastrar(session, {"titulo": "N", "dias": _dias()}, token)
    inicio = date(2030, 5, 1)
    agenda = Agenda.agendar_novena(session, novena.id, inicio, token)
    assert agenda.data_fim == date(2030, 5, 9)
    assert [agenda.calcular_dia_atual(inicio + timedelta(days=d)) for d in (-1, 0, 4, 8, 9)] == [0, 1, 5, 9, 0]
    agenda.cancelar(token)
    assert agenda.calcular_dia_atual(inicio) == 0
    with pytest.raises(DadosInvalidosError):
        _agenda_liturgia(session).calcular_dia_atual()


def test_uma_agenda_ativa_por_novena(session, token):
    teresa = _novena(session, "Novena a Santa Teresa d'Ávila")
    with pytest.raises(RegistroDuplicadoError, match="já tem uma agenda ativa"):
        Agenda.agendar_novena(session, teresa.id, date.today() + timedelta(days=20), token)
    # o próprio banco também impede (índice único parcial)
    session.add(Agenda(tipo=TipoAgenda.NOVENA, novena_id=teresa.id, status=StatusAgenda.ATIVA,
                       data_inicio=date(2031, 1, 1), data_fim=date(2031, 1, 9)))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_reagendar_depois_do_fim_conclui_a_anterior(session, token):
    novena = Novena.cadastrar(session, {"titulo": "N", "dias": _dias()}, token)
    antiga = Agenda.agendar_novena(session, novena.id, date.today() - timedelta(days=30), token)
    assert Agenda.buscar_ativa(session, novena.id) is None  # período já terminou
    nova = Agenda.agendar_novena(session, novena.id, date.today(), token)
    assert antiga.status == StatusAgenda.CONCLUIDA
    assert Agenda.buscar_ativa(session, novena.id) == nova


def test_atualizar_progresso_e_cancelar(session, token):
    agostinho = _novena(session, "Novena a Santo Agostinho")
    agenda = Agenda.buscar_ativa(session, agostinho.id)
    agenda.atualizar_progresso(date.today() - timedelta(days=2), token)
    assert agenda.calcular_dia_atual() == 3
    assert agenda.data_fim == date.today() + timedelta(days=6)
    agenda.cancelar(token)
    assert agenda.status == StatusAgenda.CANCELADA
    assert Agenda.buscar_ativa(session, agostinho.id) is None
    assert agostinho.id not in {a.novena_id for a in Agenda.listar_ativas(session, TipoAgenda.NOVENA)}
    with pytest.raises(DadosInvalidosError, match="ativas"):
        agenda.cancelar(token)
    with pytest.raises(DadosInvalidosError, match="ativas"):
        agenda.atualizar_progresso(date.today(), token)
    with pytest.raises(DadosInvalidosError, match="novena"):
        _agenda_liturgia(session).atualizar_progresso(date.today(), token)


def test_agendar_liturgias_valida_periodo(session, token):
    with pytest.raises(DadosInvalidosError, match="anterior"):
        Agenda.agendar_liturgias(session, date(2030, 1, 10), date(2030, 1, 1), token)
    agenda = Agenda.agendar_liturgias(session, "2030-01-01", "2030-01-15", token)
    assert (agenda.tipo, agenda.status, agenda.novena_id) == (TipoAgenda.LITURGIA, StatusAgenda.ATIVA, None)


@pytest.mark.parametrize("campos", [
    {"tipo": TipoAgenda.LITURGIA, "novena_id": 1, "data_inicio": date(2031, 1, 1),
     "data_fim": date(2031, 1, 2)},                                     # liturgia com novena
    {"tipo": TipoAgenda.LITURGIA, "data_inicio": date(2031, 1, 5),
     "data_fim": date(2031, 1, 1)},                                     # fim antes do início
])
def test_restricoes_check_da_agenda_no_banco(session, campos):
    session.add(Agenda(status=StatusAgenda.ATIVA, **campos))
    with pytest.raises(IntegrityError, match="CHECK"):
        session.flush()
    session.rollback()


# =========================================================================== #
# Liturgia ligada à Agenda (UML: Agenda 1 — 0..* LiturgiaDia / LiturgiaHora)
# =========================================================================== #
def test_toda_liturgia_semeada_pertence_a_agenda_de_liturgia(session):
    agenda = _agenda_liturgia(session)
    assert len(agenda.liturgias_dia) == 15 and len(agenda.liturgias_hora) == 45
    assert all(l.agenda_id == agenda.id for l in agenda.liturgias_dia)


def test_liturgia_sem_agenda_e_rejeitada_pelo_banco(session):
    session.add(LiturgiaHora(data=date(2031, 1, 1), bloco=BlocoLiturgia.LAUDES, texto="x"))
    with pytest.raises(IntegrityError, match="NOT NULL"):
        session.flush()
    session.rollback()


def test_cadastrar_liturgia_valida_a_agenda(session, token):
    agenda = Agenda.agendar_liturgias(session, date(2031, 1, 1), date(2031, 1, 7), token)
    dia = LiturgiaDia.cadastrar(session, {"data": "2031-01-03", "agenda_id": agenda.id,
                                          "evangelho": "Jo 1"}, token)
    assert dia.data == date(2031, 1, 3)
    with pytest.raises(DadosInvalidosError, match="fora do período"):
        LiturgiaDia.cadastrar(session, {"data": date(2031, 2, 1), "agenda_id": agenda.id}, token)
    novena_agenda = Agenda.buscar_ativa(session, _novena(session, "Novena a Santo Agostinho").id)
    with pytest.raises(DadosInvalidosError, match="não é de liturgia"):
        LiturgiaHora.cadastrar(session, {"data": novena_agenda.data_inicio, "agenda_id": novena_agenda.id,
                                         "bloco": "laudes", "texto": "x"}, token)
    LiturgiaHora.cadastrar(session, {"data": date(2031, 1, 3), "agenda_id": agenda.id,
                                     "bloco": BlocoLiturgia.VESPERAS, "texto": "x"}, token)
    with pytest.raises(RegistroDuplicadoError, match="Vésperas"):
        LiturgiaHora.cadastrar(session, {"data": date(2031, 1, 3), "agenda_id": agenda.id,
                                         "bloco": "vesperas", "texto": "y"}, token)
    session.rollback()


def test_atualizar_e_excluir_liturgia(session, token):
    hoje = date.today()
    dia = LiturgiaDia.buscar_data(session, hoje)
    LiturgiaDia.atualizar(session, dia.id, {"salmo": "Sl 23"}, token)
    assert LiturgiaDia.buscar_data(session, hoje).salmo == "Sl 23"
    laudes = LiturgiaHora.buscar_bloco(session, hoje, "laudes")
    LiturgiaHora.atualizar(session, laudes.id, {"texto": "novo"}, token)
    assert laudes.texto == "novo"
    with pytest.raises(DadosInvalidosError, match="fora do período"):
        LiturgiaHora.atualizar(session, laudes.id, {"data": hoje + timedelta(days=30)}, token)
    session.rollback()
    LiturgiaDia.excluir(session, dia.id, token)
    LiturgiaHora.excluir(session, LiturgiaHora.buscar_bloco(session, hoje, "laudes").id, token)
    session.commit()
    assert LiturgiaDia.buscar_data(session, hoje) is None
    assert len(LiturgiaHora.buscar_data(session, hoje)) == 2


def test_agenda_de_liturgia_cancelada_oculta_os_registros(session, token):
    hoje = date.today()
    _agenda_liturgia(session).cancelar(token)
    assert LiturgiaDia.buscar_data(session, hoje) is None
    assert LiturgiaHora.buscar_data(session, hoje) == []
    assert LiturgiaHora.buscar_bloco(session, hoje, "laudes") is None


# =========================================================================== #
# Momento do dia como enum (UML: filtrar_momento(momento: MomentoDoDia))
# =========================================================================== #
def test_filtrar_momento_aceita_enum_texto_e_id(session):
    missa = next(m for m in MomentoDia.listar_todos(session) if m.bloco == BlocoMomento.MISSA)
    por_id = {o.titulo for o in Oracao.filtrar_momento(session, missa.id)}
    assert por_id == {"Credo", "Alma de Cristo"}
    assert {o.titulo for o in Oracao.filtrar_momento(session, BlocoMomento.MISSA)} == por_id
    assert {o.titulo for o in Oracao.filtrar_momento(session, "missa")} == por_id
    with pytest.raises(DadosInvalidosError, match="Opções"):
        Oracao.filtrar_momento(session, "almoco")


def test_categorizar_aceita_lista_de_enums(session, token):
    credo = _oracao(session, "Credo")
    credo.categorizar([BlocoMomento.ANTES_DE_DORMIR, "refeicoes"], token)
    assert {m.bloco for m in credo.momentos} == {BlocoMomento.ANTES_DE_DORMIR, BlocoMomento.REFEICOES}

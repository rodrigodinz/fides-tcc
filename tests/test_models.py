from datetime import date, timedelta

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from database.connection import Base, criar_engine
from database.models import (
    Administrador, AutenticacaoError, BlocoLiturgia, BlocoMomento, DadosInvalidosError,
    DiaNovena, ForaDoIntervaloError, Livro, Liturgia, LiturgiaDia, LiturgiaHora,
    MomentoDia, Novena, Oracao, RegistroDuplicadoError, Santo,
)
from database import seeds
from database.seeds import executar_seeds, popular_banco, resolver_credenciais_admin
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


def test_busca_ignora_acentos(session):
    assert [s.nome for s in Santo.buscar_nome(session, "tomas")] == ["São Tomás de Aquino"]


def test_paginacao_respeita_limite_maximo(session):
    assert len(Santo.listar_todos(session, pagina=1, limite=2)) == 2
    assert len(Santo.listar_todos(session, pagina=1, limite=999)) <= 20


def test_santo_carrega_conteudos_vinculados(session):
    teresa = Santo.buscar_nome(session, "ávila")[0]
    assert [o.titulo for o in teresa.obter_oracoes()] == ["Nada te perturbe"]
    assert [l.titulo for l in teresa.obter_livro()] == ["O Castelo Interior"]


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
    assert {o.titulo for o in dias[0].oracoes_base()} == {"Pai Nosso", "Ave Maria"}
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


def test_liturgia_abstrata_e_intervalo(session):
    with pytest.raises(TypeError):
        Liturgia(data=date.today())
    hoje = date.today()
    assert LiturgiaDia.buscar_data(session, hoje) is not None  # vem dos seeds
    assert LiturgiaHora.buscar_bloco(session, hoje, "laudes").bloco == BlocoLiturgia.LAUDES
    assert len(Liturgia.buscar_por_data(session, hoje)) == 4  # 1 dia + 3 horas
    with pytest.raises(ForaDoIntervaloError):
        LiturgiaDia.buscar_data(session, hoje + timedelta(days=8))
    assert Liturgia._dentro_intervalo(hoje - timedelta(days=7)) is True
    assert Liturgia._dentro_intervalo(hoje + timedelta(days=8)) is False


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


def test_apagar_santo_apaga_conteudo_dele_mas_preserva_oracoes_gerais(session):
    santo = Santo.buscar_nome(session, "agostinho")[0]
    session.delete(santo)
    session.commit()
    assert Oracao.buscar_por_santo(session, santo.id) == []
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
    assert [o.titulo for o in teresa.obter_oracoes()] == ["Nada te perturbe"]
    assert [o.titulo for o in agostinho.obter_oracoes()] == ["Tarde te amei"]
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
    assert {o.titulo for o in teresinha.dias[0].oracoes_base()} == {"Pai Nosso", "Ave Maria"}
    for titulo, extra in (("Novena a Santa Teresa d'Ávila", "Nada te perturbe"),
                          ("Novena a Santo Agostinho", "Tarde te amei")):
        novena = _novena(session, titulo)
        assert {o.titulo for o in novena.dias[0].oracoes_base()} == {"Pai Nosso", "Ave Maria", "Glória ao Pai"}
        assert extra in {o.titulo for o in novena.dias[8].oracoes_base()}


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


def test_admin_legado_recebe_login_e_mantem_senha(tmp_path):
    """Banco da versão anterior: Administradores só com e-mail."""
    engine = _banco(tmp_path)
    antigo = Administrador(nome="x", login="tmp", senha_hash="x")
    antigo.definir_senha("admin123")
    with engine.begin() as con:
        con.execute(text('DROP TABLE "Administradores"'))
        con.execute(text('CREATE TABLE "Administradores" (id_administrador INTEGER NOT NULL, '
                         'nome_administrador VARCHAR NOT NULL, email_administrador VARCHAR NOT NULL, '
                         'senha_hash_administrador VARCHAR NOT NULL, PRIMARY KEY (id_administrador), '
                         'UNIQUE (email_administrador))'))
        con.execute(text('INSERT INTO "Administradores" VALUES (1, "Administrador FIDES", '
                         '"admin@fides.local", :h)'), {"h": antigo.senha_hash})
    with sessionmaker(bind=engine)() as s:
        popular_banco(s)
        popular_banco(s)  # idempotente
        admins = s.scalars(select(Administrador)).all()
        assert [(a.login, a.email) for a in admins] == [("adm", "admin@fides.local")]
        assert Administrador.autenticar(s, "adm", "admin123")  # senha anterior preservada
        with pytest.raises(AutenticacaoError):
            Administrador.autenticar(s, "adm", "senha")
        popular_banco(s, redefinir_senha_admin=True)  # regra explícita
        assert Administrador.autenticar(s, "adm", "senha")


# =========================================================================== #
# Seeds: idempotência e transação
# =========================================================================== #
def test_seeds_repetidos_nao_duplicam_nada(session):
    def contagens():
        return [session.scalar(select(func.count()).select_from(m))
                for m in (Santo, Livro, Oracao, MomentoDia, Novena, DiaNovena, Administrador)]
    antes = contagens()
    popular_banco(session)
    popular_banco(session)
    assert contagens() == antes == [5, 8, 12, 4, 3, 27, 1]


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
    assert session.scalar(select(func.count()).select_from(Liturgia)) == 15 * 4


def test_liturgia_fora_da_janela_nao_e_semeada(session):
    fora = date.today() + timedelta(days=8)
    assert session.scalar(select(func.count()).select_from(Liturgia).where(Liturgia.data == fora)) == 0


def test_seed_de_liturgia_e_idempotente_e_aceita_data_de_referencia(session):
    antes = session.scalar(select(func.count()).select_from(Liturgia))
    popular_banco(session)
    assert session.scalar(select(func.count()).select_from(Liturgia)) == antes
    popular_banco(session, data_referencia=date(2030, 1, 15))
    popular_banco(session, data_referencia=date(2030, 1, 15))
    assert session.scalar(select(func.count()).select_from(Liturgia)) == antes + 60


def test_liturgia_do_dia_duplicada_e_rejeitada_pelo_banco(session):
    session.add(LiturgiaDia(data=date.today(), primeira_leitura="x"))
    with pytest.raises(IntegrityError):
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

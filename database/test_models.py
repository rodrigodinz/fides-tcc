from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from database.connection import Base, criar_engine
from database.models import (
    Administrador, AutenticacaoError, BlocoLiturgia, BlocoMomento, DadosInvalidosError,
    DiaNovena, ForaDoIntervaloError, Livro, Liturgia, LiturgiaDia, LiturgiaHora,
    MomentoDia, Novena, Oracao, Santo,
)
from database.seeds import executar_seeds
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def session():
    engine = criar_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as s:
        executar_seeds(s)
        s.commit()
        yield s


@pytest.fixture()
def token(session):
    return Administrador.autenticar(session, "admin@fides.local", "admin123")


def test_busca_ignora_acentos(session):
    assert [s.nome for s in Santo.buscar_nome(session, "tomas")] == ["São Tomás de Aquino"]


def test_paginacao_respeita_limite_maximo(session):
    assert len(Santo.listar_todos(session, pagina=1, limite=2)) == 2
    assert len(Santo.listar_todos(session, pagina=1, limite=999)) <= 20


def test_santo_carrega_conteudos_vinculados(session):
    teresa = Santo.buscar_nome(session, "ávila")[0]
    assert [o.titulo for o in teresa.obter_oracoes()] == ["Nada te perturbe"]
    assert [l.titulo for l in teresa.obter_livro()] == ["As Moradas (O Castelo Interior)"]


def test_oracoes_basicas_e_filtro_por_momento(session):
    assert {o.titulo for o in Oracao.listar_basicas(session)} == {
        "Pai Nosso", "Ave Maria", "Credo", "Invocação ao Espírito Santo"}
    acordar = next(m for m in MomentoDia.listar_todos(session) if m.bloco == BlocoMomento.AO_ACORDAR)
    titulos = {o.titulo for o in Oracao.filtrar_momento(session, acordar.id)}
    assert "Oferecimento do dia" in titulos and "Credo" not in titulos


def test_novena_tem_nove_dias_ordenados_com_oracoes_base(session):
    novena = Novena.listar_todas(session)[0]
    dias = novena.obter_dias()
    assert [d.numero_dia for d in dias] == list(range(1, 10))
    assert {o.titulo for o in dias[0].oracoes_base()} == {"Pai Nosso", "Ave Maria"}
    assert DiaNovena.buscar_novena_dia(session, novena.id, 3).numero_dia == 3


def test_dia_da_novena_nao_repete_e_fica_entre_1_e_9(session):
    novena = Novena.listar_todas(session)[0]
    session.add(DiaNovena(novena_id=novena.id, numero_dia=10, texto_reflexao="x"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_cadastro_exige_token(session):
    with pytest.raises(AutenticacaoError):
        Santo.cadastrar(session, {"nome": "São Francisco de Assis"}, token="falso")


def test_autenticacao_invalida(session):
    with pytest.raises(AutenticacaoError):
        Administrador.autenticar(session, "admin@fides.local", "errada")


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
    session.add_all([
        LiturgiaDia(data=hoje, primeira_leitura="Is 1", salmo="Sl 1", evangelho="Mt 1",
                    segunda_leitura="  "),
        LiturgiaHora(data=hoje, bloco=BlocoLiturgia.LAUDES, texto="Laudes..."),
    ])
    session.flush()
    dia = LiturgiaDia.buscar_data(session, hoje)
    assert dia.possui_segunda_leitura() is False
    assert LiturgiaHora.buscar_bloco(session, hoje, "laudes").texto == "Laudes..."
    assert len(Liturgia.buscar_por_data(session, hoje)) == 2
    with pytest.raises(ForaDoIntervaloError):
        LiturgiaDia.buscar_data(session, hoje + timedelta(days=8))
    assert Liturgia._dentro_intervalo(hoje - timedelta(days=7)) is True


def test_seeds_sao_idempotentes(session):
    executar_seeds(session)
    session.commit()
    assert len(Santo.listar_todos(session)) == 5
    assert len(Novena.listar_todas(session)) == 1
    assert len(MomentoDia.listar_todos(session)) == 4


def test_apagar_santo_apaga_conteudo_dele_mas_preserva_oracoes_gerais(session):
    santo = Santo.buscar_nome(session, "agostinho")[0]
    session.delete(santo)
    session.commit()
    assert Oracao.buscar_por_santo(session, santo.id) == []
    assert len(Oracao.listar_basicas(session)) == 4

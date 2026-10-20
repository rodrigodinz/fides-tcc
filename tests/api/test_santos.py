import math

import pytest
from sqlalchemy import func, select

from api.services.busca import normalizar_busca
from database.models import Livro, Novena, Oracao, Santo

URL = "/api/v1/santos"


def test_listagem_com_registros_e_campos(cliente, sessao):
    r = cliente.get(URL)
    assert r.status_code == 200
    corpo = r.json()
    total = sessao.scalar(select(func.count()).select_from(Santo))
    assert corpo["total"] == total and len(corpo["itens"]) == total
    assert set(corpo) == {"itens", "pagina", "limite", "total", "total_paginas"}
    assert set(corpo["itens"][0]) == {"id", "nome", "foto_url"}
    nomes = [i["nome"] for i in corpo["itens"]]
    assert nomes == sorted(nomes)


def test_paginacao_metadados_e_cobertura_sem_repeticao(cliente, sessao):
    total = sessao.scalar(select(func.count()).select_from(Santo))
    vistos = []
    paginas = math.ceil(total / 2)
    for p in range(1, paginas + 1):
        c = cliente.get(URL, params={"pagina": p, "limite": 2}).json()
        assert c["total"] == total and c["total_paginas"] == paginas and c["limite"] == 2
        assert len(c["itens"]) <= 2
        vistos += [i["id"] for i in c["itens"]]
    assert len(vistos) == len(set(vistos)) == total


def test_pagina_alem_do_fim_retorna_200_vazio(cliente):
    r = cliente.get(URL, params={"pagina": 999})
    assert r.status_code == 200 and r.json()["itens"] == [] and r.json()["total"] > 0


@pytest.mark.parametrize("params", [{"limite": 21}, {"limite": 0}, {"limite": -1}, {"limite": "x"},
                                    {"pagina": 0}, {"pagina": -3}, {"pagina": "a"},
                                    {"pagina": 10**12}, {"q": "a" * 101}])
def test_parametros_invalidos_422_padronizado(cliente, params):
    r = cliente.get(URL, params=params)
    assert r.status_code == 422
    erro = r.json()["erro"]
    assert erro["codigo"] == "PARAMETRO_INVALIDO" and erro["detalhes"]
    assert "input" not in r.text  # não ecoa a estrutura crua do pydantic


def test_limite_maximo_20_e_aceito(cliente):
    assert cliente.get(URL, params={"limite": 20}).status_code == 200


@pytest.mark.parametrize("termo", ["tomas", "Tomás", "TOMAS", "tOmÁs", "são tomás", "SAO TOMAS", "  tomas  ", "aquino"])
def test_busca_ignora_acento_e_caixa(cliente, termo):
    nomes = [i["nome"] for i in cliente.get(URL, params={"q": termo}).json()["itens"]]
    assert nomes == ["São Tomás de Aquino"]


def test_busca_com_apostrofo_e_acento(cliente):
    nomes = [i["nome"] for i in cliente.get(URL, params={"q": "d'Ávila"}).json()["itens"]]
    assert nomes == ["Santa Teresa d'Ávila"]


def test_busca_parcial_retorna_varios_com_total_coerente(cliente, sessao):
    esperado = sessao.scalar(select(func.count()).select_from(Santo).where(Santo.nome_busca.like("%santa%")))
    c = cliente.get(URL, params={"q": "SANTA", "limite": 1}).json()
    assert c["total"] == esperado >= 2 and len(c["itens"]) == 1 and c["total_paginas"] == esperado


@pytest.mark.parametrize("termo", ["zzz", "漢字", "???"])
def test_busca_sem_resultado_200_vazio(cliente, termo):
    r = cliente.get(URL, params={"q": termo})
    assert r.status_code == 200 and r.json()["itens"] == [] and r.json()["total"] == 0


@pytest.mark.parametrize("termo", ["%", "_", "\\", "s%o"])
def test_curingas_like_sao_tratados_como_texto(cliente, termo):
    assert cliente.get(URL, params={"q": termo}).json()["itens"] == []


def test_q_vazio_equivale_a_sem_filtro(cliente, sessao):
    assert cliente.get(URL, params={"q": "  "}).json()["total"] == sessao.scalar(select(func.count()).select_from(Santo))


def test_normalizacao_da_api_coincide_com_nome_busca_do_banco(sessao):
    for santo in sessao.scalars(select(Santo)):
        assert normalizar_busca(santo.nome) == santo.nome_busca


def test_detalhe_e_relacionamentos_exatos(cliente, sessao):
    for santo in sessao.scalars(select(Santo)):
        r = cliente.get(f"{URL}/{santo.id}")
        assert r.status_code == 200
        d = r.json()
        assert d["nome"] == santo.nome and d["biografia"] == santo.biografia
        assert {o["id"] for o in d["oracoes"]} == set(sessao.scalars(select(Oracao.id).where(Oracao.santo_id == santo.id)))
        assert {n["id"] for n in d["novenas"]} == set(sessao.scalars(select(Novena.id).where(Novena.santo_id == santo.id)))
        assert {l["id"] for l in d["livros"]} == set(sessao.scalars(select(Livro.id).where(Livro.santo_id == santo.id)))


def test_detalhe_nao_mistura_conteudo_de_outro_santo_nem_orações_gerais(cliente, sessao):
    gerais = set(sessao.scalars(select(Oracao.id).where(Oracao.santo_id.is_(None))))
    por_santo = {}
    for santo in sessao.scalars(select(Santo)):
        d = cliente.get(f"{URL}/{santo.id}").json()
        ids = {o["id"] for o in d["oracoes"]}
        assert not ids & gerais
        por_santo[santo.id] = ids
    todos = [i for ids in por_santo.values() for i in ids]
    assert len(todos) == len(set(todos))  # nenhuma oração aparece em dois santos


def test_detalhe_inexistente_404(cliente):
    r = cliente.get(f"{URL}/99999")
    assert r.status_code == 404 and r.json()["erro"]["codigo"] == "RECURSO_NAO_ENCONTRADO"


@pytest.mark.parametrize("valor", ["abc", "0", "-1", "1.5"])
def test_detalhe_id_invalido_422(cliente, valor):
    assert cliente.get(f"{URL}/{valor}").status_code == 422


def test_falha_de_consulta_e_500_padronizado_e_nao_503(cliente_sem_tabelas):
    r = cliente_sem_tabelas.get(URL)
    assert r.status_code == 500
    assert r.json()["erro"]["codigo"] == "ERRO_INTERNO"
    assert "no such table" not in r.text and "Santos" not in r.text


def test_banco_inacessivel_em_rota_de_dados_e_503(cliente_banco_inacessivel):
    r = cliente_banco_inacessivel.get(URL)
    assert r.status_code == 503 and r.json()["erro"]["codigo"] == "SERVICO_INDISPONIVEL"

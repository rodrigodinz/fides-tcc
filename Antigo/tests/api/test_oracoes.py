import math

import pytest
from sqlalchemy import func, select

from database.models import MomentoDia, Oracao, Santo

URL = "/api/v1/oracoes"


def _ids(corpo):
    return {i["id"] for i in corpo["itens"]}


def _todos(cliente, **params):
    """Percorre todas as páginas (limite 5) e devolve os itens."""
    itens, pagina = [], 1
    while True:
        c = cliente.get(URL, params={**params, "pagina": pagina, "limite": 5}).json()
        itens += c["itens"]
        if pagina >= c["total_paginas"]:
            return itens, c
        pagina += 1


def test_listagem_campos_e_total(cliente, sessao):
    c = cliente.get(URL).json()
    assert c["total"] == sessao.scalar(select(func.count()).select_from(Oracao))
    item = c["itens"][0]
    assert set(item) == {"id", "titulo", "texto", "basica", "santo", "momentos"}
    titulos = [i["titulo"] for i in c["itens"]]
    assert titulos == sorted(titulos)


def test_paginacao_percorre_tudo_sem_repetir(cliente, sessao):
    itens, ultimo = _todos(cliente)
    total = sessao.scalar(select(func.count()).select_from(Oracao))
    assert len(itens) == total == ultimo["total"]
    assert len({i["id"] for i in itens}) == total
    assert ultimo["total_paginas"] == math.ceil(total / 5)


def test_filtro_basica_us05(cliente, sessao):
    esperado = set(sessao.scalars(select(Oracao.id).where(Oracao.basica.is_(True))))
    itens, _ = _todos(cliente, basica="true")
    assert {i["id"] for i in itens} == esperado and esperado
    assert all(i["basica"] for i in itens)
    nao_basicas, _ = _todos(cliente, basica="false")
    assert not any(i["basica"] for i in nao_basicas)
    assert len(itens) + len(nao_basicas) == sessao.scalar(select(func.count()).select_from(Oracao))


def test_filtro_por_cada_momento_us06(cliente, sessao):
    momentos = cliente.get("/api/v1/momentos").json()
    assert len(momentos) == len(sessao.scalars(select(MomentoDia)).all())
    for m in momentos:
        esperado = {o.id for o in sessao.get(MomentoDia, m["id"]).oracoes}
        itens, c = _todos(cliente, momento_id=m["id"])
        assert {i["id"] for i in itens} == esperado
        assert c["total"] == len(esperado)
        assert all(m["id"] in [x["id"] for x in i["momentos"]] for i in itens)


def test_filtro_por_santo(cliente, sessao):
    for santo in sessao.scalars(select(Santo)):
        esperado = set(sessao.scalars(select(Oracao.id).where(Oracao.santo_id == santo.id)))
        itens, _ = _todos(cliente, santo_id=santo.id)
        assert {i["id"] for i in itens} == esperado
        assert all(i["santo"]["id"] == santo.id for i in itens)


def test_filtros_combinados_e_total_coerente(cliente, sessao):
    momentos = cliente.get("/api/v1/momentos").json()
    achou_nao_trivial = False
    for m in momentos:
        for basica in (True, False):
            esperado = {o.id for o in sessao.get(MomentoDia, m["id"]).oracoes if o.basica is basica}
            itens, c = _todos(cliente, momento_id=m["id"], basica=str(basica).lower())
            assert {i["id"] for i in itens} == esperado and c["total"] == len(esperado)
            achou_nao_trivial |= bool(esperado)
    assert achou_nao_trivial
    santo = sessao.scalar(select(Santo).where(Santo.nome_busca.like("%agostinho%")))
    itens, _ = _todos(cliente, santo_id=santo.id, basica="true")
    assert itens == []  # orações de santo não são básicas
    itens, _ = _todos(cliente, santo_id=santo.id, basica="false")
    assert len(itens) >= 1


def test_oracao_geral_tem_santo_nulo_e_de_santo_tem_referencia(cliente, sessao):
    itens, _ = _todos(cliente)
    for i in itens:
        no_banco = sessao.get(Oracao, i["id"])
        assert (i["santo"] is None) == (no_banco.santo_id is None)
        assert {m["id"] for m in i["momentos"]} == {m.id for m in no_banco.momentos}


def test_sem_resultados_200_vazio(cliente):
    for params in ({"santo_id": 99999}, {"momento_id": 99999}, {"pagina": 999}):
        r = cliente.get(URL, params=params)
        assert r.status_code == 200 and r.json()["itens"] == []


@pytest.mark.parametrize("params", [{"basica": "talvez"}, {"momento_id": 0}, {"momento_id": "x"},
                                    {"santo_id": -1}, {"limite": 50}])
def test_parametros_invalidos_422(cliente, params):
    r = cliente.get(URL, params=params)
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"


def test_momentos_codigos_e_nomes(cliente):
    momentos = cliente.get("/api/v1/momentos").json()
    assert [m["codigo"] for m in momentos] == ["ao_acordar", "refeicoes", "missa", "antes_de_dormir"]
    assert [m["nome"] for m in momentos] == ["Ao acordar", "Refeições", "Missa", "Antes de dormir"]
    assert all(set(m) == {"id", "codigo", "nome"} for m in momentos)

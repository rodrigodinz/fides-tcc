import pytest
from sqlalchemy import func, select

from database.models import DiaNovena, Novena

URL = "/api/v1/novenas"


def test_listagem_e_campos(cliente, sessao):
    c = cliente.get(URL).json()
    assert c["total"] == sessao.scalar(select(func.count()).select_from(Novena))
    for item in c["itens"]:
        assert set(item) == {"id", "titulo", "descricao", "santo", "total_dias"}
        assert item["total_dias"] == 9
        assert sessao.get(Novena, item["id"]).santo_id == item["santo"]["id"]


def test_paginacao_e_filtro_por_santo(cliente, sessao):
    assert len(cliente.get(URL, params={"limite": 1}).json()["itens"]) == 1
    for n in sessao.scalars(select(Novena)):
        c = cliente.get(URL, params={"santo_id": n.santo_id}).json()
        esperado = sessao.scalar(select(func.count()).select_from(Novena).where(Novena.santo_id == n.santo_id))
        assert c["total"] == esperado and n.id in {i["id"] for i in c["itens"]}
    assert cliente.get(URL, params={"santo_id": 99999}).json()["itens"] == []


def test_detalhe_da_novena(cliente, sessao):
    for n in sessao.scalars(select(Novena)):
        d = cliente.get(f"{URL}/{n.id}").json()
        assert d["titulo"] == n.titulo and d["total_dias"] == 9 and d["santo"]["nome"] == n.santo.nome


def test_dias_ordenados_de_1_a_9(cliente, sessao):
    for n in sessao.scalars(select(Novena)):
        d = cliente.get(f"{URL}/{n.id}/dias").json()
        assert d["novena"]["id"] == n.id and d["total_dias"] == 9
        assert [x["numero_dia"] for x in d["dias"]] == list(range(1, 10))
        assert {x["id"] for x in d["dias"]} == {x.id for x in n.dias}


def test_dia_especifico_conteudo_e_oracoes_do_proprio_dia(cliente, sessao):
    for n in sessao.scalars(select(Novena)):
        for numero in range(1, 10):
            r = cliente.get(f"{URL}/{n.id}/dias/{numero}")
            assert r.status_code == 200
            d = r.json()
            banco = DiaNovena.buscar_novena_dia(sessao, n.id, numero)
            assert d["texto_reflexao"] == banco.texto_reflexao
            assert d["numero_dia"] == numero and d["total_dias"] == 9
            assert {o["id"] for o in d["oracoes"]} == {o.id for o in banco.oracoes}
            assert d["novena"] == {"id": n.id, "titulo": n.titulo}


def test_dias_diferentes_tem_reflexoes_diferentes(cliente, sessao):
    n = sessao.scalar(select(Novena))
    textos = {cliente.get(f"{URL}/{n.id}/dias/{i}").json()["texto_reflexao"] for i in range(1, 10)}
    assert len(textos) == 9


def test_navegacao_anterior_e_proximo(cliente, sessao):
    n = sessao.scalar(select(Novena))
    for numero in range(1, 10):
        d = cliente.get(f"{URL}/{n.id}/dias/{numero}").json()
        assert d["dia_anterior"] == (numero - 1 if numero > 1 else None)
        assert d["proximo_dia"] == (numero + 1 if numero < 9 else None)


@pytest.mark.parametrize("numero", [0, 10, -1, 100, "x"])
def test_dia_fora_do_intervalo_422(cliente, sessao, numero):
    n = sessao.scalar(select(Novena))
    r = cliente.get(f"{URL}/{n.id}/dias/{numero}")
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"


@pytest.mark.parametrize("caminho", ["/99999", "/99999/dias", "/99999/dias/1"])
def test_novena_inexistente_404(cliente, caminho):
    r = cliente.get(URL + caminho)
    assert r.status_code == 404 and r.json()["erro"]["codigo"] == "RECURSO_NAO_ENCONTRADO"


def test_nao_ha_endpoint_de_progresso_ou_pedidos(cliente):
    rotas = set(cliente.get("/openapi.json").json()["paths"])
    assert not any("progresso" in r or "pedido" in r for r in rotas)

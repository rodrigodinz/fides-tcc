from datetime import date, timedelta

import pytest
from sqlalchemy import func, select

from database.models import Conteudo_Dia_Novena, Novena
from database.seeds import Agenda_Novenas

Url = "/api/v1/novenas"


def test_listagem_e_campos(cliente, sessao):
    c = cliente.get(Url).json()
    assert c["total_registros_filtros"] == sessao.scalar(select(func.count()).select_from(Novena))
    for item in c["itens"]:
        assert set(item) == {"id", "titulo", "descricao", "santo", "total_dias", "agenda"}
        assert item["total_dias"] == 9
        assert sessao.get(Novena, item["id"]).santo_id == item["santo"]["id"]


def test_paginacao_e_filtro_por_santo(cliente, sessao):
    assert len(cliente.get(Url, params={"limite": 1}).json()["itens"]) == 1
    for n in sessao.scalars(select(Novena)):
        c = cliente.get(Url, params={"santo_id": n.santo_id}).json()
        esperado = sessao.scalar(select(func.count()).select_from(Novena).where(Novena.santo_id == n.santo_id))
        assert c["total_registros_filtros"] == esperado and n.id in {i["id"] for i in c["itens"]}
    assert cliente.get(Url, params={"santo_id": 99999}).json()["itens"] == []


def test_detalhe_da_novena(cliente, sessao):
    for n in sessao.scalars(select(Novena)):
        d = cliente.get(f"{Url}/{n.id}").json()
        assert d["titulo"] == n.titulo and d["total_dias"] == 9 and d["santo"]["nome"] == n.santo.nome


def test_dias_ordenados_de_1_a_9(cliente, sessao):
    for n in sessao.scalars(select(Novena)):
        d = cliente.get(f"{Url}/{n.id}/dias").json()
        assert d["novena"]["id"] == n.id and d["total_dias"] == 9
        assert [x["numero_do_dia"] for x in d["dias"]] == list(range(1, 10))
        assert {x["id"] for x in d["dias"]} == {x.id for x in n.dias}


def test_dia_especifico_conteudo_e_oracoes_do_proprio_dia(cliente, sessao):
    for n in sessao.scalars(select(Novena)):
        for numero in range(1, 10):
            r = cliente.get(f"{Url}/{n.id}/dias/{numero}")
            assert r.status_code == 200
            d = r.json()
            banco = Conteudo_Dia_Novena.buscar_dia_da_novena(sessao, n.id, numero)
            assert d["texto_reflexao"] == banco.texto_reflexao
            assert d["numero_do_dia"] == numero and d["total_dias"] == 9
            assert {o["id"] for o in d["oracoes"]} == {o.id for o in banco.oracoes}
            assert d["novena"] == {"id": n.id, "titulo": n.titulo}


def test_dias_diferentes_tem_reflexoes_diferentes(cliente, sessao):
    n = sessao.scalar(select(Novena))
    textos = {cliente.get(f"{Url}/{n.id}/dias/{i}").json()["texto_reflexao"] for i in range(1, 10)}
    assert len(textos) == 9


def test_navegacao_anterior_e_proximo(cliente, sessao):
    n = sessao.scalar(select(Novena))
    for numero in range(1, 10):
        d = cliente.get(f"{Url}/{n.id}/dias/{numero}").json()
        assert d["dia_anterior"] == (numero - 1 if numero > 1 else None)
        assert d["proximo_dia"] == (numero + 1 if numero < 9 else None)


@pytest.mark.parametrize("numero", [0, 10, -1, 100, "x"])
def test_dia_fora_do_intervalo_422(cliente, sessao, numero):
    n = sessao.scalar(select(Novena))
    r = cliente.get(f"{Url}/{n.id}/dias/{numero}")
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"


@pytest.mark.parametrize("caminho", ["/99999", "/99999/dias", "/99999/dias/1"])
def test_novena_inexistente_404(cliente, caminho):
    r = cliente.get(Url + caminho)
    assert r.status_code == 404 and r.json()["erro"]["codigo"] == "RECURSO_NAO_ENCONTRADO"


def test_nao_ha_endpoint_de_progresso_ou_pedidos(cliente):
    rotas = set(cliente.get("/openapi.json").json()["paths"])
    assert not any("progresso" in r or "pedido" in r for r in rotas)


def _esperado(titulo, hoje=None):
    hoje = hoje or date.today()
    inicio = hoje + timedelta(days=Agenda_Novenas[titulo])
    dia = (hoje - inicio).days + 1
    return inicio, dia if 1 <= dia <= 9 else 0


def test_agenda_de_cada_novena_reflete_os_seeds(cliente):
    itens = {i["titulo"]: i for i in cliente.get(Url).json()["itens"]}
    assert set(itens) == set(Agenda_Novenas)
    for titulo, item in itens.items():
        inicio, dia = _esperado(titulo)
        agenda = item["agenda"]
        assert set(agenda) == {"id", "data_inicio", "data_fim", "dia_atual", "situacao"}
        assert agenda["data_inicio"] == inicio.isoformat()
        assert agenda["data_fim"] == (inicio + timedelta(days=8)).isoformat()
        assert agenda["dia_atual"] == dia
        assert agenda["situacao"] == ("em_andamento" if dia else "agendada")
    assert itens["Novena a Santa Teresinha"]["agenda"]["dia_atual"] == 5
    assert itens["Novena a Santa Teresa d'Ávila"]["agenda"]["dia_atual"] == 1
    assert itens["Novena a Santo Agostinho"]["agenda"]["situacao"] == "agendada"


def test_detalhe_traz_a_mesma_agenda_da_listagem(cliente):
    for item in cliente.get(Url).json()["itens"]:
        assert cliente.get(f"{Url}/{item['id']}").json() == item


def test_calendario_dos_nove_dias_com_datas(cliente, sessao):
    for n in sessao.scalars(select(Novena)):
        d = cliente.get(f"{Url}/{n.id}/dias").json()
        inicio = date.fromisoformat(d["agenda"]["data_inicio"])
        assert [x["data"] for x in d["dias"]] == [(inicio + timedelta(days=i)).isoformat() for i in range(9)]


def test_dia_especifico_informa_data_e_dia_atual(cliente, sessao):
    n = sessao.scalar(select(Novena).where(Novena.titulo == "Novena a Santa Teresinha"))
    inicio, dia_atual = _esperado(n.titulo)
    d = cliente.get(f"{Url}/{n.id}/dias/3").json()
    assert d["data"] == (inicio + timedelta(days=2)).isoformat()
    assert d["dia_atual"] == dia_atual == 5


def test_agenda_cancelada_some_do_progresso(cliente_cancelado):
    itens = {i["titulo"]: i for i in cliente_cancelado.get(Url).json()["itens"]}
    teresa = itens["Novena a Santa Teresa d'Ávila"]
    assert teresa["agenda"] is None
    dias = cliente_cancelado.get(f"{Url}/{teresa['id']}/dias").json()
    assert dias["agenda"] is None and all(x["data"] is None for x in dias["dias"])
    dia = cliente_cancelado.get(f"{Url}/{teresa['id']}/dias/1").json()
    assert dia["data"] is None and dia["dia_atual"] is None
    assert itens["Novena a Santa Teresinha"]["agenda"] is not None


def test_novena_sem_santo_nao_quebra_e_tem_santo_nulo(cliente_novena_sem_santo):
    c = cliente_novena_sem_santo
    itens = {i["titulo"]: i for i in c.get(Url).json()["itens"]}
    nova = itens["Novena de teste sem santo"]
    assert nova["santo"] is None and nova["total_dias"] == 9
    assert nova["agenda"]["dia_atual"] == 1 and nova["agenda"]["situacao"] == "em_andamento"
    assert c.get(f"{Url}/{nova['id']}").json()["santo"] is None
    assert c.get(f"{Url}/{nova['id']}/dias/9").json()["texto_reflexao"] == "Reflexão 9"

from datetime import date, timedelta

import pytest

from database.seeds import Agenda_Novenas

Url = "/api/v1/agenda"


def _d(offset):
    return date.today() + timedelta(days=offset)


def _novenas_esperadas(data, referencia=None):
    referencia = referencia or date.today()
    esperado = {}
    for titulo, deslocamento in Agenda_Novenas.items():
        dia = (data - (referencia + timedelta(days=deslocamento))).days + 1
        if 1 <= dia <= 9:
            esperado[titulo] = dia
    return esperado


def test_agenda_de_hoje_campos_e_conteudo(cliente):
    r = cliente.get(Url)
    assert r.status_code == 200
    a = r.json()
    assert set(a) == {"data", "periodo", "liturgia_do_dia", "liturgia_das_horas", "novenas_em_andamento", "aviso"}
    assert a["data"] == date.today().isoformat()
    assert a["liturgia_do_dia"]["primeira_leitura"] and a["liturgia_do_dia"]["evangelho"]
    assert [h["bloco"]["codigo"] for h in a["liturgia_das_horas"]] == ["laudes", "horas_medias", "vesperas"]
    assert "demonstração" in a["aviso"].lower()
    em_andamento = {n["novena"]["titulo"]: n["dia_atual"] for n in a["novenas_em_andamento"]}
    assert em_andamento == {"Novena a Santa Teresinha": 5, "Novena a Santa Teresa d'Ávila": 1}


@pytest.mark.parametrize("offset", range(-7, 8))
def test_toda_a_janela_novenas_conferem_com_a_agenda(cliente, offset):
    data = _d(offset)
    a = cliente.get(Url, params={"data": data.isoformat()}).json()
    assert a["data"] == data.isoformat()
    assert {n["novena"]["titulo"]: n["dia_atual"] for n in a["novenas_em_andamento"]} == _novenas_esperadas(data)
    for n in a["novenas_em_andamento"]:
        inicio = date.fromisoformat(n["data_inicio"])
        assert (data - inicio).days + 1 == n["dia_atual"] and n["total_dias"] == 9
        assert set(n["novena"]) == {"id", "titulo", "santo"}
    assert a["liturgia_do_dia"] is not None and len(a["liturgia_das_horas"]) == 3


def test_segunda_leitura_aos_domingos_na_agenda(cliente):
    for offset in range(-7, 8):
        data = _d(offset)
        dia = cliente.get(Url, params={"data": data.isoformat()}).json()["liturgia_do_dia"]
        assert dia["tem_segunda_leitura_no_dia"] is (data.weekday() == 6)
        assert (dia["segunda_leitura"] is not None) is (data.weekday() == 6)


@pytest.mark.parametrize("offset", [-8, 8, 40])
def test_fora_da_janela_400(cliente, offset):
    r = cliente.get(Url, params={"data": _d(offset).isoformat()})
    assert r.status_code == 400 and r.json()["erro"]["codigo"] == "DATA_FORA_DO_INTERVALO"


@pytest.mark.parametrize("valor", ["abc", "2026-02-30", "25/11/2026"])
def test_data_malformada_422(cliente, valor):
    r = cliente.get(Url, params={"data": valor})
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"


def test_dia_da_janela_sem_liturgia_nao_e_erro_na_agenda(cliente_liturgia_defasada):
    referencia = _d(-3)
    data = _d(6)
    a = cliente_liturgia_defasada.get(Url, params={"data": data.isoformat()}).json()
    assert a["liturgia_do_dia"] is None and a["liturgia_das_horas"] == []
    assert ({n["novena"]["titulo"]: n["dia_atual"] for n in a["novenas_em_andamento"]}
            == _novenas_esperadas(data, referencia))


def test_agendas_canceladas_nao_aparecem(cliente_cancelado):
    a = cliente_cancelado.get(Url).json()
    assert a["liturgia_do_dia"] is None and a["liturgia_das_horas"] == []
    titulos = {n["novena"]["titulo"] for n in a["novenas_em_andamento"]}
    assert titulos == {"Novena a Santa Teresinha"}


def test_novena_sem_santo_na_agenda(cliente_novena_sem_santo):
    a = cliente_novena_sem_santo.get(Url).json()
    nova = [n for n in a["novenas_em_andamento"] if n["novena"]["titulo"] == "Novena de teste sem santo"]
    assert len(nova) == 1 and nova[0]["novena"]["santo"] is None and nova[0]["dia_atual"] == 1

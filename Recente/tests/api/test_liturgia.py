from datetime import date, timedelta

import pytest

from database.models import BlocoLiturgia, Periodo_Disponivel_De_Liturgias

Dia, Horas = "/api/v1/liturgia/dia", "/api/v1/liturgia/horas"
Codigos = ["laudes", "horas_medias", "vesperas"]


def _d(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


def test_dia_padrao_e_hoje_com_campos_e_aviso(cliente):
    r = cliente.get(Dia)
    assert r.status_code == 200
    d = r.json()
    assert d["data"] == date.today().isoformat()
    assert set(d) == {"data", "periodo", "santo_celebrado", "primeira_leitura", "salmo", "evangelho",
                      "segunda_leitura", "tem_segunda_leitura_no_dia", "aviso"}
    assert d["primeira_leitura"] and d["salmo"] and d["evangelho"]
    assert "demonstração" in d["aviso"].lower()
    assert "[Demonstração]" in d["primeira_leitura"]


def test_periodo_na_resposta_usa_regra_do_modelo(cliente):
    periodo = cliente.get(Dia).json()["periodo"]
    hoje = date.today()
    assert Periodo_Disponivel_De_Liturgias == 7
    assert periodo == {"hoje": hoje.isoformat(), "inicio": _d(-7), "fim": _d(7)}


@pytest.mark.parametrize("offset", range(-7, 8))
def test_toda_a_janela_e_consultavel(cliente, offset):
    assert cliente.get(Dia, params={"data": _d(offset)}).status_code == 200
    r = cliente.get(Horas, params={"data": _d(offset)})
    assert r.status_code == 200 and len(r.json()["horas"]) == 3


@pytest.mark.parametrize("offset", [-8, 8, -30, 365])
@pytest.mark.parametrize("url", [Dia, Horas])
def test_fora_da_janela_400_com_codigo_proprio(cliente, url, offset):
    r = cliente.get(url, params={"data": _d(offset)})
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "DATA_FORA_DO_INTERVALO"
    assert "fora do intervalo" in r.json()["erro"]["mensagem"]


@pytest.mark.parametrize("valor", ["abc", "2026-13-45", "13/10/2026", "2026-02-30", "", "hoje"])
@pytest.mark.parametrize("url", [Dia, Horas])
def test_data_malformada_422(cliente, url, valor):
    r = cliente.get(url, params={"data": valor})
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"


def test_horas_em_ordem_canonica_independente_da_insercao(cliente):
    h = cliente.get(Horas).json()
    assert [x["bloco"]["codigo"] for x in h["horas"]] == Codigos
    assert [x["bloco"]["nome"] for x in h["horas"]] == [b.value for b in BlocoLiturgia]
    assert h["aviso"] and set(h) == {"data", "periodo", "horas", "aviso"}


@pytest.mark.parametrize("codigo", Codigos)
def test_filtro_por_bloco(cliente, codigo):
    h = cliente.get(Horas, params={"bloco": codigo}).json()
    assert [x["bloco"]["codigo"] for x in h["horas"]] == [codigo]


def test_bloco_invalido_422(cliente):
    assert cliente.get(Horas, params={"bloco": "completas"}).status_code == 422


def test_segunda_leitura_so_quando_cadastrada(cliente):
    domingos = comuns = 0
    for offset in range(-7, 8):
        data = date.today() + timedelta(days=offset)
        d = cliente.get(Dia, params={"data": data.isoformat()}).json()
        if data.weekday() == 6:
            domingos += 1
            assert d["tem_segunda_leitura_no_dia"] is True and d["segunda_leitura"]
        else:
            comuns += 1
            assert d["tem_segunda_leitura_no_dia"] is False and d["segunda_leitura"] is None
    assert domingos >= 2 and comuns >= 10


def test_data_valida_sem_registro_e_404_diferente_de_fora_da_janela(cliente_liturgia_defasada):
    c = cliente_liturgia_defasada
    for url in (Dia, Horas):
        sem_registro = c.get(url, params={"data": _d(6)})
        assert sem_registro.status_code == 404
        assert sem_registro.json()["erro"]["codigo"] == "LITURGIA_NAO_CADASTRADA"
        fora = c.get(url, params={"data": _d(8)})
        assert fora.status_code == 400 and fora.json()["erro"]["codigo"] == "DATA_FORA_DO_INTERVALO"
    assert c.get(Dia, params={"data": _d(4)}).status_code == 200


def test_agenda_de_liturgia_cancelada_oculta_a_liturgia(cliente_cancelado):
    for url in (Dia, Horas):
        r = cliente_cancelado.get(url)
        assert r.status_code == 404 and r.json()["erro"]["codigo"] == "LITURGIA_NAO_CADASTRADA"
    assert cliente_cancelado.get(Dia, params={"data": _d(9)}).status_code == 400


def test_bloco_sem_registro_404_com_bloco(cliente_liturgia_defasada):
    r = cliente_liturgia_defasada.get(Horas, params={"data": _d(6), "bloco": "laudes"})
    assert r.status_code == 404 and r.json()["erro"]["codigo"] == "LITURGIA_NAO_CADASTRADA"

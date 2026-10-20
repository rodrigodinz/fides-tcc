from datetime import date, timedelta

import pytest

from database.models import BlocoLiturgia, INTERVALO_LITURGIA_DIAS

DIA, HORAS = "/api/v1/liturgia/dia", "/api/v1/liturgia/horas"
CODIGOS = ["laudes", "horas_medias", "vesperas"]


def _d(offset):
    return (date.today() + timedelta(days=offset)).isoformat()


def test_dia_padrao_e_hoje_com_campos_e_aviso(cliente):
    r = cliente.get(DIA)
    assert r.status_code == 200
    d = r.json()
    assert d["data"] == date.today().isoformat()
    assert set(d) == {"data", "intervalo", "santo_celebrado", "primeira_leitura", "salmo", "evangelho",
                      "segunda_leitura", "possui_segunda_leitura", "aviso"}
    assert d["primeira_leitura"] and d["salmo"] and d["evangelho"]
    assert "demonstração" in d["aviso"].lower()
    assert "[Demonstração]" in d["primeira_leitura"]  # o texto vindo do banco não é "maquiado"


def test_intervalo_na_resposta_usa_regra_do_modelo(cliente):
    i = cliente.get(DIA).json()["intervalo"]
    hoje = date.today()
    assert INTERVALO_LITURGIA_DIAS == 7
    assert i == {"hoje": hoje.isoformat(), "inicio": _d(-7), "fim": _d(7)}


@pytest.mark.parametrize("offset", range(-7, 8))
def test_toda_a_janela_e_consultavel(cliente, offset):
    assert cliente.get(DIA, params={"data": _d(offset)}).status_code == 200
    r = cliente.get(HORAS, params={"data": _d(offset)})
    assert r.status_code == 200 and len(r.json()["horas"]) == 3


@pytest.mark.parametrize("offset", [-8, 8, -30, 365])
@pytest.mark.parametrize("url", [DIA, HORAS])
def test_fora_da_janela_400_com_codigo_proprio(cliente, url, offset):
    r = cliente.get(url, params={"data": _d(offset)})
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "DATA_FORA_DO_INTERVALO"
    assert "demonstração" in r.json()["erro"]["mensagem"]


@pytest.mark.parametrize("valor", ["abc", "2026-13-45", "13/10/2026", "2026-02-30", "", "hoje"])
@pytest.mark.parametrize("url", [DIA, HORAS])
def test_data_malformada_422(cliente, url, valor):
    r = cliente.get(url, params={"data": valor})
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"


def test_horas_em_ordem_canonica_independente_da_insercao(cliente):
    h = cliente.get(HORAS).json()
    assert [x["bloco"]["codigo"] for x in h["horas"]] == CODIGOS
    assert [x["bloco"]["nome"] for x in h["horas"]] == [b.value for b in BlocoLiturgia]
    assert h["aviso"] and h["avisos_integridade"] == []


@pytest.mark.parametrize("codigo", CODIGOS)
def test_filtro_por_bloco(cliente, codigo):
    h = cliente.get(HORAS, params={"bloco": codigo}).json()
    assert [x["bloco"]["codigo"] for x in h["horas"]] == [codigo]


def test_bloco_invalido_422(cliente):
    assert cliente.get(HORAS, params={"bloco": "completas"}).status_code == 422


def test_segunda_leitura_so_quando_cadastrada(cliente):
    domingos = comuns = 0
    for offset in range(-7, 8):
        data = date.today() + timedelta(days=offset)
        d = cliente.get(DIA, params={"data": data.isoformat()}).json()
        if data.weekday() == 6:  # os seeds cadastram segunda leitura apenas aos domingos
            domingos += 1
            assert d["possui_segunda_leitura"] is True and d["segunda_leitura"]
        else:
            comuns += 1
            assert d["possui_segunda_leitura"] is False and d["segunda_leitura"] is None
    assert domingos >= 2 and comuns >= 10


def test_data_valida_sem_registro_e_404_diferente_de_fora_da_janela(cliente_liturgia_defasada):
    c = cliente_liturgia_defasada
    for url in (DIA, HORAS):
        sem_registro = c.get(url, params={"data": _d(6)})  # dentro da janela, mas o seed só cobre até hoje+4
        assert sem_registro.status_code == 404
        assert sem_registro.json()["erro"]["codigo"] == "LITURGIA_NAO_CADASTRADA"
        fora = c.get(url, params={"data": _d(8)})
        assert fora.status_code == 400 and fora.json()["erro"]["codigo"] == "DATA_FORA_DO_INTERVALO"
    assert c.get(DIA, params={"data": _d(4)}).status_code == 200  # último dia semeado


def test_bloco_repetido_nao_causa_500_e_o_problema_e_sinalizado(cliente_hora_duplicada):
    r = cliente_hora_duplicada.get(HORAS)
    assert r.status_code == 200
    h = r.json()
    assert [x["bloco"]["codigo"] for x in h["horas"]] == CODIGOS  # um por bloco, em ordem
    assert len(h["avisos_integridade"]) == 1 and "Laudes" in h["avisos_integridade"][0]
    laudes = h["horas"][0]["texto"]
    assert "duplicada" not in laudes  # prevalece o registro mais antigo (menor id)
    filtrado = cliente_hora_duplicada.get(HORAS, params={"bloco": "laudes"}).json()
    assert len(filtrado["horas"]) == 1 and filtrado["avisos_integridade"]
    outro = cliente_hora_duplicada.get(HORAS, params={"bloco": "vesperas"}).json()
    assert outro["avisos_integridade"] == []

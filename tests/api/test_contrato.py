"""Testes transversais: contrato HTTP, formato de erros e ausência de dados sensíveis."""
import re

import pytest

ROTAS_LISTA = ["/api/v1/santos", "/api/v1/oracoes", "/api/v1/novenas", "/api/v1/livros"]
ROTAS_OK = ROTAS_LISTA + ["/health", "/api/v1/momentos", "/api/v1/santos/1", "/api/v1/novenas/1",
                          "/api/v1/novenas/1/dias", "/api/v1/novenas/1/dias/1", "/api/v1/livros/1",
                          "/api/v1/liturgia/dia", "/api/v1/liturgia/horas"]
ROTAS_ERRO = ["/api/v1/santos/999999", "/api/v1/santos?limite=99", "/api/v1/liturgia/dia?data=2000-01-01",
              "/api/v1/liturgia/dia?data=xx", "/api/v1/novenas/1/dias/10", "/api/v1/inexistente"]

# Termos que jamais devem aparecer em respostas públicas.
PROIBIDOS = [r"senha", r"password", r"token", r"pbkdf2", r"senha_hash", r"secret", r"login", r"administrador",
             r"traceback", r"sqlalchemy", r"sqlite", r"select\s", r"\.db\b", r"fides_", r"[A-Za-z]:\\", r"/home/", r"/tmp/"]


@pytest.mark.parametrize("url", ROTAS_OK)
def test_respostas_json_sem_dados_sensiveis(cliente, url):
    r = cliente.get(url)
    assert r.status_code == 200, url
    assert r.headers["content-type"].startswith("application/json")
    for padrao in PROIBIDOS:
        assert not re.search(padrao, r.text, re.IGNORECASE), f"{url} contém /{padrao}/"


@pytest.mark.parametrize("url", ROTAS_ERRO)
def test_erros_seguem_o_formato_padrao_e_nao_vazam(cliente, url):
    r = cliente.get(url)
    assert 400 <= r.status_code < 500
    corpo = r.json()
    assert set(corpo) == {"erro"} and set(corpo["erro"]) == {"codigo", "mensagem", "detalhes"}
    assert isinstance(corpo["erro"]["detalhes"], list) and corpo["erro"]["mensagem"]
    for padrao in PROIBIDOS:
        assert not re.search(padrao, r.text, re.IGNORECASE), f"{url} contém /{padrao}/"


@pytest.mark.parametrize("url", ROTAS_LISTA)
def test_envelope_de_paginacao_e_limite_maximo(cliente, url):
    c = cliente.get(url).json()
    assert set(c) == {"itens", "pagina", "limite", "total", "total_paginas"}
    assert c["limite"] == 20 and len(c["itens"]) <= 20
    assert cliente.get(url, params={"limite": 21}).status_code == 422
    assert cliente.get(url, params={"limite": 20}).status_code == 200


@pytest.mark.parametrize("url", ROTAS_LISTA)
def test_total_paginas_vazio_e_zero(cliente, url):
    c = cliente.get(url, params={"santo_id": 99999} if url != "/api/v1/santos" else {"q": "zzzz"}).json()
    assert c["itens"] == [] and c["total"] == 0 and c["total_paginas"] == 0


def test_rotas_de_dados_sao_publicas_sem_autenticacao(cliente):
    for url in ROTAS_OK:
        assert cliente.get(url).status_code == 200  # sem cabeçalho Authorization


def test_openapi_documenta_o_formato_de_erro(cliente):
    esquema = cliente.get("/openapi.json").json()
    assert "ErroResposta" in esquema["components"]["schemas"]
    resp_422 = esquema["paths"]["/api/v1/santos"]["get"]["responses"]["422"]
    assert "ErroResposta" in str(resp_422)

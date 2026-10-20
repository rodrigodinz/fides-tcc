"""Infraestrutura: saúde, erros padronizados, CORS, estáticos, fuso horário, somente leitura."""
import os
import time
from datetime import date

import pytest
from fastapi.testclient import TestClient

from api.config import aplicar_fuso_horario
from api.main import create_app

from fides_helpers import montar_cliente


def test_aplicacao_inicializa_e_expoe_documentacao(cliente):
    assert cliente.get("/docs").status_code == 200
    assert cliente.get("/openapi.json").status_code == 200


def test_health_ok(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "banco": "ok"}


def test_health_503_quando_banco_inacessivel(cliente_banco_inacessivel):
    r = cliente_banco_inacessivel.get("/health")
    assert r.status_code == 503
    assert r.json()["erro"]["codigo"] == "SERVICO_INDISPONIVEL"


def test_rota_inexistente_404_padronizado(cliente):
    r = cliente.get("/api/v1/nao-existe")
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "ROTA_NAO_ENCONTRADA"


def test_metodo_nao_permitido_405_padronizado(cliente):
    r = cliente.post("/health")
    assert r.status_code == 405
    assert r.json()["erro"]["codigo"] == "METODO_NAO_PERMITIDO"
    assert "GET" in r.headers.get("allow", "")


def test_erro_inesperado_vira_500_sem_vazar_detalhes():
    app = create_app()

    @app.get("/_explode")
    def _explode():  # rota existente só neste teste
        raise RuntimeError("segredo-interno C:\\caminho\\local SELECT * FROM x")

    r = TestClient(app, raise_server_exceptions=False).get("/_explode", headers={"Origin": "http://localhost:5173"})
    assert r.status_code == 500
    corpo = r.text
    assert r.json()["erro"]["codigo"] == "ERRO_INTERNO"
    for proibido in ("segredo-interno", "Traceback", "SELECT", "caminho"):
        assert proibido not in corpo
    # o 500 também precisa carregar CORS, senão o navegador não consegue ler a mensagem
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_somente_get_no_openapi(cliente):
    for caminho, operacoes in cliente.get("/openapi.json").json()["paths"].items():
        assert set(operacoes) == {"get"}, f"{caminho} expõe {set(operacoes)}"


@pytest.mark.parametrize("metodo", ["post", "put", "patch", "delete"])
@pytest.mark.parametrize("caminho", ["/health", "/api/v1/santos", "/api/v1/oracoes", "/api/v1/novenas",
                                     "/api/v1/livros", "/api/v1/liturgia/dia", "/api/v1/santos/1"])
def test_metodos_de_escrita_rejeitados(cliente, metodo, caminho):
    assert getattr(cliente, metodo)(caminho).status_code in (404, 405)


@pytest.mark.parametrize("caminho", ["/admin", "/api/v1/admin", "/api/v1/login", "/api/v1/auth"])
def test_sem_rotas_administrativas(cliente, caminho):
    assert cliente.get(caminho).status_code == 404


# ----------------------------- CORS -----------------------------
def test_cors_origem_permitida(cliente):
    r = cliente.get("/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_origem_nao_permitida(cliente):
    r = cliente.get("/health", headers={"Origin": "http://site-malicioso.test"})
    assert "access-control-allow-origin" not in r.headers


def test_cors_preflight_get_permitido(cliente):
    r = cliente.options("/api/v1/santos", headers={"Origin": "http://localhost:3000",
                                                   "Access-Control-Request-Method": "GET"})
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_preflight_metodo_de_escrita_negado(cliente):
    r = cliente.options("/api/v1/santos", headers={"Origin": "http://localhost:3000",
                                                   "Access-Control-Request-Method": "POST"})
    assert r.status_code == 400


def test_cors_origens_configuraveis(monkeypatch, fabrica):
    monkeypatch.setenv("FIDES_CORS_ORIGINS", "https://fides.exemplo.com.br/")
    c = montar_cliente(fabrica)
    ok = c.get("/health", headers={"Origin": "https://fides.exemplo.com.br"})
    assert ok.headers["access-control-allow-origin"] == "https://fides.exemplo.com.br"
    negado = c.get("/health", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-origin" not in negado.headers


# ------------------------- Arquivos estáticos -------------------------
def test_static_serve_arquivo_do_diretorio_configurado(monkeypatch, tmp_path, fabrica):
    (tmp_path / "santos").mkdir()
    (tmp_path / "santos" / "teste.txt").write_text("conteudo")
    monkeypatch.setenv("FIDES_STATIC_DIR", str(tmp_path))
    c = montar_cliente(fabrica)
    r = c.get("/static/santos/teste.txt")
    assert r.status_code == 200 and r.text == "conteudo"


def test_static_arquivo_ausente_e_404_padronizado(cliente):
    r = cliente.get("/static/santos/tomas-de-aquino.jpg")
    assert r.status_code == 404
    assert "erro" in r.json()


def test_static_diretorio_inexistente_nao_derruba_a_api(monkeypatch, tmp_path, fabrica):
    monkeypatch.setenv("FIDES_STATIC_DIR", str(tmp_path / "nao_existe"))
    c = montar_cliente(fabrica)
    assert c.get("/static/x.jpg").status_code == 404
    assert c.get("/health").status_code == 200


# ----------------------------- Fuso horário -----------------------------
@pytest.mark.skipif(not hasattr(time, "tzset"), reason="time.tzset indisponível nesta plataforma")
def test_fuso_horario_e_aplicado_ao_processo():
    original = os.environ.get("TZ")
    try:
        assert aplicar_fuso_horario("Pacific/Kiritimati") is True  # UTC+14
        assert time.localtime().tm_gmtoff == 14 * 3600
        assert aplicar_fuso_horario("America/Sao_Paulo") is True  # UTC-3 (sem horário de verão desde 2019)
        assert time.localtime().tm_gmtoff == -3 * 3600
        assert isinstance(date.today(), date)
        assert aplicar_fuso_horario("Isto/Nao_Existe") is False  # inválido: mantém o anterior
        assert time.localtime().tm_gmtoff == -3 * 3600
    finally:
        if original is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original
        time.tzset()

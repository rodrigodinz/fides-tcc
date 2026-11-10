import json
import socket
import threading
import time

import pytest
import uvicorn

from site_helpers import montar_aplicacao_de_teste

# Os testes do site precisam do Playwright e do Chromium:
#   pip install playwright
#   python -m playwright install chromium
# Sem eles, estes testes são pulados (os do banco e da API continuam rodando).
sync_api = pytest.importorskip("playwright.sync_api", reason="instale o Playwright para testar o site")


def _porta_livre() -> int:
    with socket.socket() as soquete:
        soquete.bind(("127.0.0.1", 0))
        return soquete.getsockname()[1]


@pytest.fixture(scope="session")
def endereco_do_site(tmp_path_factory):
    """Sobe a API + site de verdade (uvicorn) numa porta livre, com um banco temporário populado."""
    app = montar_aplicacao_de_teste(tmp_path_factory)
    porta = _porta_livre()
    servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=porta, log_level="warning"))
    linha_de_execucao = threading.Thread(target=servidor.run, daemon=True)
    linha_de_execucao.start()
    limite = time.time() + 15
    while not servidor.started:
        if time.time() > limite:
            raise RuntimeError("o servidor de teste não subiu")
        time.sleep(0.05)
    yield f"http://127.0.0.1:{porta}"
    servidor.should_exit = True
    linha_de_execucao.join(timeout=10)


@pytest.fixture(scope="session")
def navegador():
    with sync_api.sync_playwright() as playwright:
        try:
            chromium = playwright.chromium.launch()
        except Exception as erro:  # navegador não instalado
            pytest.skip(f"Chromium do Playwright indisponível ({erro.__class__.__name__}): rode 'python -m playwright install chromium'")
        yield chromium
        chromium.close()


class PaginaDeTeste:
    """Página do navegador + o que aconteceu nela (erros de JavaScript e requisições à API)."""

    def __init__(self, pagina, endereco_do_site):
        self.pagina = pagina
        self.endereco_do_site = endereco_do_site
        self.erros_de_javascript = []
        self.chamadas_a_api = []
        self.respostas_inventadas = []
        pagina.on("pageerror", lambda erro: self.erros_de_javascript.append(str(erro)))
        pagina.on("request", lambda requisicao: self.chamadas_a_api.append(requisicao.url) if "/api/v1/" in requisicao.url else None)

    def abrir(self, caminho):
        self.pagina.goto(self.endereco_do_site + caminho, wait_until="networkidle")
        return self.pagina

    def responder_api(self, trecho_da_url, corpo=None, status=200, funcao=None):
        """Troca a resposta de uma rota da API por uma resposta inventada (para simular cenários).
        Vale a primeira regra cadastrada cujo trecho aparece na URL; sem regra, a API real responde."""
        if not self.respostas_inventadas:
            self.pagina.route(lambda url: "/api/v1/" in url, self._atender_pela_primeira_regra)
        self.respostas_inventadas.append((f"/api/v1{trecho_da_url}", corpo, status, funcao))

    def _atender_pela_primeira_regra(self, rota):
        for trecho, corpo, status, funcao in self.respostas_inventadas:
            if trecho in rota.request.url:
                if funcao is not None:
                    return funcao(rota)
                return rota.fulfill(status=status, content_type="application/json", body=json.dumps(corpo))
        return rota.continue_()

def _criar_pagina(navegador, endereco_do_site, viewport):
    contexto = navegador.new_context(viewport=viewport)
    pagina = PaginaDeTeste(contexto.new_page(), endereco_do_site)
    return contexto, pagina


@pytest.fixture()
def site(navegador, endereco_do_site):
    contexto, pagina = _criar_pagina(navegador, endereco_do_site, {"width": 1280, "height": 800})
    yield pagina
    contexto.close()
    assert pagina.erros_de_javascript == [], f"erros de JavaScript: {pagina.erros_de_javascript}"


@pytest.fixture()
def site_no_celular(navegador, endereco_do_site):
    contexto, pagina = _criar_pagina(navegador, endereco_do_site, {"width": 390, "height": 844})
    yield pagina
    contexto.close()
    assert pagina.erros_de_javascript == [], f"erros de JavaScript: {pagina.erros_de_javascript}"


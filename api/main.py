"""Execução (na raiz do repositório): uvicorn api.main:app --reload
Depois é só abrir http://127.0.0.1:8000 no navegador. a API e o site saem do mesmo servidor."""
import mimetypes
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import aplicar_fuso_horario, ler_configuracoes
from .errors import Respostas_De_Erro, CapturaDeErrosInternos, registrar_tratadores_de_erro
from .routes import agenda, health, liturgia, livros, novenas, oracoes, santos


# No Windows, o registro do sistema às vezes diz que .js é "text/plain" e o navegador se recusa a rodar o script. Aqui fixamos o tipo certo de cada arquivo do site.
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("font/woff2", ".woff2")

# serve as imagens em /static; se a pasta não existir responde 404 em vez de derrubar a API
class ArquivosEstaticosTolerantes(StaticFiles):
    async def check_config(self) -> None:
        self.config_checked = True

    async def get_response(self, path, scope):
        if not self.directory or not os.path.isdir(self.directory):
            raise StarletteHTTPException(status_code=404)
        return await super().get_response(path, scope)


Caminhos_Da_Api = ("/api/", "/api", "/health", "/static/", "/docs", "/redoc", "/openapi.json")


# Liga a pasta frontend/ ao servidor. Ela vira a "rota padrão"
def servir_site(app: FastAPI, diretorio_do_frontend) -> None:
    # html=True: "/" entrega o index.html e um endereço inexistente entrega o 404.html
    arquivos_do_site = StaticFiles(directory=diretorio_do_frontend, html=True)
    rota_padrao_da_api = app.router.default

    async def entregar_pagina_ou_erro(scope, receive, send):
        if scope["type"] == "http" and not scope["path"].startswith(Caminhos_Da_Api):
            await arquivos_do_site(scope, receive, send)
        else:
            await rota_padrao_da_api(scope, receive, send)

    app.router.default = entregar_pagina_ou_erro


def criar_aplicacao() -> FastAPI:
    configuracoes = ler_configuracoes()
    aplicar_fuso_horario(configuracoes.fuso_horario)

    app = FastAPI(title="Fides API", version="0.2.0",
                  responses={422: Respostas_De_Erro[422], 500: Respostas_De_Erro[500]})

    app.add_middleware(CapturaDeErrosInternos)  # qualquer exceção não tratada vira um 500 em JSON
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(configuracoes.origens_permitidas),
        allow_methods=["GET"],
        allow_headers=["Accept", "Accept-Language", "Content-Type"],
        allow_credentials=False,
    )
    registrar_tratadores_de_erro(app)

    app.include_router(health.router)
    # todas as rotas de conteúdo ficam na /api/v1
    for modulo_de_rotas in (santos, oracoes, novenas, livros, liturgia, agenda):
        app.include_router(modulo_de_rotas.router, prefix="/api/v1")

    # check_dir=False → a API sobe mesmo sem o diretório/imagens (ai vai aparecer o erro 404).
    app.mount("/static", ArquivosEstaticosTolerantes(directory=configuracoes.diretorio_estatico, check_dir=False),
              name="static")

    # site (páginas .html, css, js, fontes e imagens): http://127.0.0.1:8000/ abre o index.html
    if configuracoes.diretorio_do_frontend.is_dir():
        servir_site(app, configuracoes.diretorio_do_frontend)
    return app


app = criar_aplicacao()  # é esse objeto que o uvicorn carrega (api.main:app)

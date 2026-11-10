"""Execução (na raiz do repositório): uvicorn api.main:app --reload"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import aplicar_fuso_horario, ler_configuracoes
from .errors import Respostas_De_Erro, CapturaDeErrosInternos, registrar_tratadores_de_erro
from .routes import agenda, health, liturgia, livros, novenas, oracoes, santos


# serve as imagens em /static; se a pasta não existir responde 404 em vez de derrubar a API
class ArquivosEstaticosTolerantes(StaticFiles):
    async def check_config(self) -> None:
        self.config_checked = True

    async def get_response(self, path, scope):
        if not self.directory or not os.path.isdir(self.directory):
            raise StarletteHTTPException(status_code=404)
        return await super().get_response(path, scope)


def criar_aplicacao() -> FastAPI:
    configuracoes = ler_configuracoes()
    aplicar_fuso_horario(configuracoes.fuso_horario)

    app = FastAPI(title="Fides API", version="0.2.0",
                  responses={422: Respostas_De_Erro[422], 500: Respostas_De_Erro[500]})

    app.add_middleware(CapturaDeErrosInternos)  # qualquer exceção não tratada vira um 500 em JSON
    # CORS: libera o front-end (outra porta/origem) a chamar a API; só GET no MVP
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(configuracoes.origens_permitidas),
        allow_methods=["GET"],
        allow_headers=["Accept", "Accept-Language", "Content-Type"],
        allow_credentials=False,
    )
    registrar_tratadores_de_erro(app)

    app.include_router(health.router)
    # todas as rotas de conteúdo ficam sob /api/v1
    for modulo_de_rotas in (santos, oracoes, novenas, livros, liturgia, agenda):
        app.include_router(modulo_de_rotas.router, prefix="/api/v1")

    # check_dir=False: a API sobe mesmo sem o diretório/imagens (ai vai aparecer o erro 404).
    app.mount("/static", ArquivosEstaticosTolerantes(directory=configuracoes.diretorio_estatico, check_dir=False),
              name="static")
    return app


app = criar_aplicacao()  # é esse objeto que o uvicorn carrega (api.main:app)

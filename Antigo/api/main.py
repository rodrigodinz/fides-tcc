"""Aplicação FastAPI do Fides. Execução: ``uvicorn api.main:app --reload`` (na raiz)."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import aplicar_fuso_horario, get_settings
from .errors import RESPOSTAS_ERRO, CapturaErrosInternos, registrar_handlers
from .routes import agenda, health, liturgia, livros, novenas, oracoes, santos

DESCRICAO = ()


class StaticFilesTolerante(StaticFiles):
    """StaticFiles que responde 404 (e não 500) se o diretório não existir.

    A API deve funcionar mesmo sem o diretório configurado em FIDES_STATIC_DIR
    ou sem alguma das imagens dos santos.
    """

    async def check_config(self) -> None:
        # O Starlette lança RuntimeError aqui quando o diretório não existe;
        # a verificação passa a ser feita por requisição, em get_response.
        self.config_checked = True

    async def get_response(self, path, scope):
        if not self.directory or not os.path.isdir(self.directory):
            raise StarletteHTTPException(status_code=404)
        return await super().get_response(path, scope)


def create_app() -> FastAPI:
    config = get_settings()
    aplicar_fuso_horario(config.timezone)

    app = FastAPI(title="Fides API", version="0.2.0", description=DESCRICAO,
                  responses={422: RESPOSTAS_ERRO[422], 500: RESPOSTAS_ERRO[500]})

    app.add_middleware(CapturaErrosInternos)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.cors_origins),
        allow_methods=["GET"],
        allow_headers=["Accept", "Accept-Language", "Content-Type"],
        allow_credentials=False,
    )
    registrar_handlers(app)

    app.include_router(health.router)
    for modulo in (santos, oracoes, novenas, livros, liturgia, agenda):
        app.include_router(modulo.router, prefix="/api/v1")

    # check_dir=False: a API sobe mesmo sem o diretório/imagens (ai vai aparecer o erro 404).
    app.mount("/static", StaticFilesTolerante(directory=config.static_dir, check_dir=False), name="static")
    return app


app = create_app()

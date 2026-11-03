"""Convenção centralizada de erros: {"erro": {"codigo", "mensagem", "detalhes"}}."""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from database.models import ForaDoIntervaloError

from .schemas.comum import ErroResposta

logger = logging.getLogger("fides.api")


class ApiError(Exception):
    def __init__(self, status_code: int, codigo: str, mensagem: str, detalhes: list | None = None):
        super().__init__(mensagem)
        self.status_code = status_code
        self.codigo = codigo
        self.mensagem = mensagem
        self.detalhes = detalhes or []


def nao_encontrado(recurso: str) -> ApiError:
    return ApiError(404, "RECURSO_NAO_ENCONTRADO", f"{recurso} não encontrado(a).")


def resposta_erro(status: int, codigo: str, mensagem: str, detalhes: list | None = None,
                  headers: dict | None = None) -> JSONResponse:
    corpo = {"erro": {"codigo": codigo, "mensagem": mensagem, "detalhes": detalhes or []}}
    return JSONResponse(status_code=status, content=corpo, headers=headers)


# Documentação OpenAPI dos erros (reaproveitada pelas rotas).
RESPOSTAS_ERRO = {
    400: {"model": ErroResposta, "description": "Requisição inválida segundo regra de negócio."},
    404: {"model": ErroResposta, "description": "Recurso inexistente."},
    422: {"model": ErroResposta, "description": "Parâmetro malformado."},
    500: {"model": ErroResposta, "description": "Falha interna."},
    503: {"model": ErroResposta, "description": "Banco indisponível."},
}

_TEMPLATES_VALIDACAO = {
    "int_parsing": "Deve ser um número inteiro.",
    "int_from_float": "Deve ser um número inteiro.",
    "bool_parsing": "Deve ser true ou false.",
    "greater_than_equal": "Deve ser maior ou igual a {ge}.",
    "less_than_equal": "Deve ser menor ou igual a {le}.",
    "string_too_long": "Deve ter no máximo {max_length} caracteres.",
    "enum": "Valor não permitido. Valores aceitos: {expected}.",
    "date_parsing": "Data inválida. Use o formato AAAA-MM-DD.",
    "date_from_datetime_parsing": "Data inválida. Use o formato AAAA-MM-DD.",
    "date_from_datetime_inexact": "Data inválida. Use o formato AAAA-MM-DD.",
    "date_type": "Data inválida. Use o formato AAAA-MM-DD.",
    "missing": "Parâmetro obrigatório.",
}


def _mensagem_validacao(erro: dict) -> str:
    modelo = _TEMPLATES_VALIDACAO.get(erro.get("type"))
    if modelo:
        try:
            return modelo.format(**(erro.get("ctx") or {}))
        except (KeyError, IndexError):
            pass
    return erro.get("msg", "Valor inválido.")


# Mensagens do SQLite que indicam banco inacessível (e não bug de consulta).
_SINAIS_INDISPONIBILIDADE = ("unable to open database", "database is locked",
                             "disk i/o error", "database or disk is full", "readonly database")


def _banco_indisponivel(exc: SQLAlchemyError) -> bool:
    if getattr(exc, "connection_invalidated", False):
        return True
    if isinstance(exc, OperationalError):
        texto = str(getattr(exc, "orig", exc)).lower()
        return any(sinal in texto for sinal in _SINAIS_INDISPONIBILIDADE)
    return False


class CapturaErrosInternos(BaseHTTPMiddleware):
    """Transforma exceções não previstas em 500 JSON padronizado.

    Fica dentro do CORS (que é registrado depois), para que até o 500
    carregue os cabeçalhos CORS e o navegador consiga ler a mensagem.
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Erro interno em %s %s", request.method, request.url.path)
            return resposta_erro(500, "ERRO_INTERNO",
                                 "Ocorreu um erro interno. Tente novamente em instantes.")


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_req: Request, exc: ApiError):
        return resposta_erro(exc.status_code, exc.codigo, exc.mensagem, exc.detalhes)

    @app.exception_handler(ForaDoIntervaloError)
    async def _fora_intervalo(_req: Request, exc: ForaDoIntervaloError):
        return resposta_erro(400, "DATA_FORA_DO_INTERVALO", str(exc))

    @app.exception_handler(RequestValidationError)
    async def _validacao(_req: Request, exc: RequestValidationError):
        detalhes = []
        for erro in exc.errors():
            loc = [str(p) for p in erro.get("loc", ())]
            detalhes.append({"local": loc[0] if loc else None,
                             "campo": ".".join(loc[1:]) or None,
                             "mensagem": _mensagem_validacao(erro)})
        return resposta_erro(422, "PARAMETRO_INVALIDO", "Um ou mais parâmetros são inválidos.", detalhes)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_req: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return resposta_erro(404, "ROTA_NAO_ENCONTRADA", "Recurso ou rota não encontrado(a).")
        if exc.status_code == 405:
            return resposta_erro(405, "METODO_NAO_PERMITIDO",
                                 "Método HTTP não permitido. A API do MVP é somente leitura (GET).",
                                 headers=dict(exc.headers or {}))
        return resposta_erro(exc.status_code, "ERRO_HTTP", "A requisição não pôde ser atendida.")

    @app.exception_handler(SQLAlchemyError)
    async def _banco(_req: Request, exc: SQLAlchemyError):
        if _banco_indisponivel(exc):
            logger.error("Banco indisponível: %s", type(exc).__name__)
            return resposta_erro(503, "SERVICO_INDISPONIVEL",
                                 "Serviço temporariamente indisponível. Tente novamente em instantes.")
        logger.exception("Falha de consulta ao banco")
        return resposta_erro(500, "ERRO_INTERNO",
                             "Ocorreu um erro interno. Tente novamente em instantes.")

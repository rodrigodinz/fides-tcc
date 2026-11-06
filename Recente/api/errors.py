import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from database.models import Erro_Da_Liturgia_Fora_Da_Data_Permitida

from .schemas.comum import RespostaDeErro

logger = logging.getLogger("fides.api")


# erro que as rotas e serviços lançam; vira o JSON {"erro": {...}} com o status certo
class Erro_Da_Api(Exception):
    def __init__(self, status_code: int, codigo: str, mensagem: str, detalhes: list | None = None):
        super().__init__(mensagem)
        self.status_code = status_code
        self.codigo = codigo
        self.mensagem = mensagem
        self.detalhes = detalhes or []


def erro_recurso_nao_encontrado(recurso: str) -> Erro_Da_Api:
    return Erro_Da_Api(404, "RECURSO_NAO_ENCONTRADO", f"{recurso} não encontrado(a).")


def montar_resposta_de_erro(status: int, codigo: str, mensagem: str, detalhes: list | None = None,
                            headers: dict | None = None) -> JSONResponse:
    corpo = {"erro": {"codigo": codigo, "mensagem": mensagem, "detalhes": detalhes or []}}
    return JSONResponse(status_code=status, content=corpo, headers=headers)


Respostas_De_Erro = {
    400: {"model": RespostaDeErro, "description": "Requisição inválida segundo regra de negócio."},
    404: {"model": RespostaDeErro, "description": "Recurso inexistente."},
    422: {"model": RespostaDeErro, "description": "Parâmetro malformado."},
    500: {"model": RespostaDeErro, "description": "Falha interna."},
    503: {"model": RespostaDeErro, "description": "Banco indisponível."},
}

_Mensagens_De_Validacao = {
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


def _traduzir_mensagem_de_validacao(erro: dict) -> str:
    modelo_da_mensagem = _Mensagens_De_Validacao.get(erro.get("type"))
    if modelo_da_mensagem:
        try:
            return modelo_da_mensagem.format(**(erro.get("ctx") or {}))
        except (KeyError, IndexError):
            pass
    return erro.get("msg", "Valor inválido.")


_Sinais_De_Banco_Indisponivel = ("unable to open database", "database is locked",
                                 "disk i/o error", "database or disk is full", "readonly database")


def _banco_esta_indisponivel(excecao: SQLAlchemyError) -> bool:
    if getattr(excecao, "connection_invalidated", False):
        return True
    if isinstance(excecao, OperationalError):
        texto_do_erro = str(getattr(excecao, "orig", excecao)).lower()
        return any(sinal in texto_do_erro for sinal in _Sinais_De_Banco_Indisponivel)
    return False


class CapturaDeErrosInternos(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Erro interno em %s %s", request.method, request.url.path)
            return montar_resposta_de_erro(500, "ERRO_INTERNO",
                                           "Ocorreu um erro interno. Tente novamente em instantes.")


# cada exception_handler converte um tipo de exceção na resposta JSON padronizada
def registrar_tratadores_de_erro(app: FastAPI) -> None:
    @app.exception_handler(Erro_Da_Api)
    async def _tratar_erro_da_api(_requisicao: Request, excecao: Erro_Da_Api):
        return montar_resposta_de_erro(excecao.status_code, excecao.codigo, excecao.mensagem, excecao.detalhes)

    @app.exception_handler(Erro_Da_Liturgia_Fora_Da_Data_Permitida)
    async def _tratar_liturgia_fora_da_data(_requisicao: Request,
                                            excecao: Erro_Da_Liturgia_Fora_Da_Data_Permitida):
        return montar_resposta_de_erro(400, "DATA_FORA_DO_INTERVALO", str(excecao))

    @app.exception_handler(RequestValidationError)
    async def _tratar_erro_de_validacao(_requisicao: Request, excecao: RequestValidationError):
        detalhes = []
        for erro in excecao.errors():
            caminho_do_erro = [str(parte) for parte in erro.get("loc", ())]
            detalhes.append({"onde": caminho_do_erro[0] if caminho_do_erro else None,
                             "campo": ".".join(caminho_do_erro[1:]) or None,
                             "mensagem": _traduzir_mensagem_de_validacao(erro)})
        return montar_resposta_de_erro(422, "PARAMETRO_INVALIDO", "Um ou mais parâmetros são inválidos.", detalhes)

    @app.exception_handler(StarletteHTTPException)
    async def _tratar_erro_http(_requisicao: Request, excecao: StarletteHTTPException):
        if excecao.status_code == 404:
            return montar_resposta_de_erro(404, "ROTA_NAO_ENCONTRADA", "Recurso ou rota não encontrado(a).")
        if excecao.status_code == 405:
            return montar_resposta_de_erro(405, "METODO_NAO_PERMITIDO",
                                           "Método HTTP não permitido. A API do MVP é somente leitura (GET).",
                                           headers=dict(excecao.headers or {}))
        return montar_resposta_de_erro(excecao.status_code, "ERRO_HTTP", "A requisição não pôde ser atendida.")

    @app.exception_handler(SQLAlchemyError)
    async def _tratar_erro_do_banco(_requisicao: Request, excecao: SQLAlchemyError):
        if _banco_esta_indisponivel(excecao):
            logger.error("Banco indisponível: %s", type(excecao).__name__)
            return montar_resposta_de_erro(503, "SERVICO_INDISPONIVEL",
                                           "Serviço temporariamente indisponível. Tente novamente em instantes.")
        logger.exception("Falha de consulta ao banco")
        return montar_resposta_de_erro(500, "ERRO_INTERNO",
                                       "Ocorreu um erro interno. Tente novamente em instantes.")

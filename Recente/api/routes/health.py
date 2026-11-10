import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import Respostas_De_Erro, Erro_Da_Api
from ..schemas.comum import RespostaDeSaude

logger = logging.getLogger("fides.api")
# rota fora do /api/v1: serve para verificar se a API e o banco estão no ar
router = APIRouter(tags=["Infraestrutura"])


@router.get("/health", response_model=RespostaDeSaude,
            responses={503: Respostas_De_Erro[503]}, summary="Verifica a aplicação e o banco")
def verificar_saude(session: Annotated[Session, Depends(get_session)]):
    try:
        session.execute(text("SELECT 1"))  # consulta mínima: se o banco responder, está ok
    except SQLAlchemyError as excecao:
        logger.error("Falha na verificação do banco: %s", type(excecao).__name__)
        raise Erro_Da_Api(503, "SERVICO_INDISPONIVEL",
                          "Serviço temporariamente indisponível. Tente novamente em instantes.") from excecao
    return RespostaDeSaude(status="ok", banco="ok")

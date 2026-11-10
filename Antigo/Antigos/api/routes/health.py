"""Verificação de saúde da aplicação e do banco."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import RESPOSTAS_ERRO, ApiError
from ..schemas.comum import SaudeResposta

logger = logging.getLogger("fides.api")
router = APIRouter(tags=["Infraestrutura"])


@router.get("/health", response_model=SaudeResposta,
            responses={503: RESPOSTAS_ERRO[503]}, summary="Verifica aplicação e banco")
def health(session: Annotated[Session, Depends(get_session)]):
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.error("Falha na verificação do banco: %s", type(exc).__name__)
        raise ApiError(503, "SERVICO_INDISPONIVEL",
                       "Serviço temporariamente indisponível. Tente novamente em instantes.") from exc
    return SaudeResposta(status="ok", banco="ok")

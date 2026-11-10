"""US14-US17: Liturgia das Horas e Liturgia do Dia (dados de demonstração)."""
import enum
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import BlocoLiturgia

from ..errors import RESPOSTAS_ERRO
from ..schemas.liturgia import LiturgiaDiaResposta, LiturgiaHorasResposta
from ..services import liturgia as servico

router = APIRouter(prefix="/liturgia", tags=["Liturgia"], responses=RESPOSTAS_ERRO)
Sessao = Annotated[Session, Depends(get_session)]
Data = Annotated[date | None, Query(description="AAAA-MM-DD. Padrão: hoje. Janela: hoje ± 7 dias.")]


class BlocoParam(str, enum.Enum):
    laudes = "laudes"
    horas_medias = "horas_medias"
    vesperas = "vesperas"


@router.get("/horas", response_model=LiturgiaHorasResposta, summary="Liturgia das Horas (US14, US17)")
def liturgia_das_horas(session: Sessao, data: Data = None,
                       bloco: Annotated[BlocoParam | None, Query(description="Filtra um bloco canônico.")] = None):
    return servico.consultar_horas(session, data, BlocoLiturgia[bloco.name.upper()] if bloco else None)


@router.get("/dia", response_model=LiturgiaDiaResposta, summary="Liturgia do Dia (US15, US16, US17)")
def liturgia_do_dia(session: Sessao, data: Data = None):
    return servico.consultar_dia(session, data)

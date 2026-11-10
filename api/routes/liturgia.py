import enum
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import BlocoLiturgia

from ..errors import Respostas_De_Erro
from ..schemas.liturgia import RespostaLiturgiaDasHoras, RespostaLiturgiaDoDia
from ..services import liturgia as servico

router = APIRouter(prefix="/liturgia", tags=["Liturgia"], responses=Respostas_De_Erro)
# Depends(get_session): o FastAPI abre uma sessão do banco por requisição e fecha no final
Sessao = Annotated[Session, Depends(get_session)]
# Query(...) diz que o valor vem da URL (?data=); o FastAPI já valida o formato da data
DataConsultada = Annotated[date | None, Query(description="AAAA-MM-DD. Padrão: hoje. Período: hoje ± 7 dias.")]


# valores aceitos em ?bloco= (qualquer outro devolve 422)
class ParametroBloco(str, enum.Enum):
    laudes = "laudes"
    horas_medias = "horas_medias"
    vesperas = "vesperas"


# GET /api/v1/liturgia/horas
@router.get("/horas", response_model=RespostaLiturgiaDasHoras, summary="Liturgia das Horas")
def liturgia_das_horas(session: Sessao, data: DataConsultada = None,
                       bloco: Annotated[ParametroBloco | None, Query(description="Filtra um bloco.")] = None):
    # converte o texto da URL (laudes) no enum do banco (BlocoLiturgia.LAUDES)
    bloco_da_liturgia = BlocoLiturgia[bloco.name.upper()] if bloco else None
    return servico.consultar_liturgia_das_horas(session, data, bloco_da_liturgia)


# GET /api/v1/liturgia/dia
@router.get("/dia", response_model=RespostaLiturgiaDoDia, summary="Liturgia do Dia")
def liturgia_do_dia(session: Sessao, data: DataConsultada = None):
    return servico.consultar_liturgia_do_dia(session, data)

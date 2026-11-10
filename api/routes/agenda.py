from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import Respostas_De_Erro
from ..schemas.agenda import ConteudosDoDia
from ..services import agenda_dia as servico

router = APIRouter(prefix="/agenda", tags=["Agenda"], responses=Respostas_De_Erro)
# Depends(get_session) (o FastAPI abre uma sessão do banco por requisição e fecha no final)
Sessao = Annotated[Session, Depends(get_session)]


# GET /api/v1/agenda?data=AAAA-MM-DD -> response_model define o formato (schema) da resposta
@router.get("", response_model=ConteudosDoDia, summary="Conteúdos agendados para uma data")
def ver_conteudos_do_dia(
    session: Sessao,
    data: Annotated[date | None, Query(description="AAAA-MM-DD. Padrão: hoje. Período: hoje ± 7 dias.")] = None,
):
    # a rota só recebe e valida os parâmetros; a regra fica no serviço
    return servico.consultar_conteudos_do_dia(session, data)

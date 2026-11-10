"""Agenda do dia: liturgia da data e novenas em andamento (UC08, UC14-UC16; US08, US14-US17).

A agenda é global, definida pelo administrador (no MVP, pelos seeds). Não há
progresso individual do fiel no servidor.
"""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import RESPOSTAS_ERRO
from ..schemas.agenda import AgendaDoDia
from ..services import agenda_dia as servico

router = APIRouter(prefix="/agenda", tags=["Agenda"], responses=RESPOSTAS_ERRO)
Sessao = Annotated[Session, Depends(get_session)]


@router.get("", response_model=AgendaDoDia, summary="Conteúdo agendado para uma data")
def agenda_do_dia(
    session: Sessao,
    data: Annotated[date | None, Query(description="AAAA-MM-DD. Padrão: hoje. Janela: hoje ± 7 dias.")] = None,
):
    return servico.consultar(session, data)

"""US07-US10: catálogo de novenas, dias, progresso pela agenda e navegação entre dias.

O "Dia X de 9" vem da Agenda global definida pelo administrador (no MVP, pelos
seeds), por meio de ``Agenda.buscar_ativa`` e ``Agenda.calcular_dia_atual``.
Não há progresso individual do fiel nem pedidos de oração no servidor: pedidos
e marcações pessoais ficam no dispositivo (estado do React). Ver docs/API.md.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import DIAS_DA_NOVENA

from ..errors import RESPOSTAS_ERRO
from ..schemas.comum import Pagina
from ..schemas.novenas import DiaNovenaDetalhe, DiasDaNovena, NovenaItem
from ..services import novenas as servico
from ..services.paginacao import Paginacao

router = APIRouter(prefix="/novenas", tags=["Novenas"], responses=RESPOSTAS_ERRO)
Sessao = Annotated[Session, Depends(get_session)]
IdNovena = Annotated[int, Path(ge=1)]


@router.get("", response_model=Pagina[NovenaItem], summary="Catálogo de novenas ativas")
def listar_novenas(session: Sessao, paginacao: Paginacao,
                   santo_id: Annotated[int | None, Query(ge=1)] = None):
    return servico.listar(session, paginacao, santo_id)


@router.get("/{novena_id}", response_model=NovenaItem, summary="Detalhe e progresso da novena")
def detalhar_novena(session: Sessao, novena_id: IdNovena):
    return servico.detalhar(session, novena_id)


@router.get("/{novena_id}/dias", response_model=DiasDaNovena, summary="Calendário dos nove dias")
def listar_dias(session: Sessao, novena_id: IdNovena):
    return servico.listar_dias(session, novena_id)


@router.get("/{novena_id}/dias/{numero_dia}", response_model=DiaNovenaDetalhe,
            summary="Conteúdo do dia")
def obter_dia(session: Sessao, novena_id: IdNovena,
              numero_dia: Annotated[int, Path(ge=1, le=DIAS_DA_NOVENA)]):
    return servico.obter_dia(session, novena_id, numero_dia)

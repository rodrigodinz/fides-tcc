"""US07-US10: catálogo de novenas, dias e navegação entre dias.

O progresso individual (dia atual, dias concluídos, pedidos) NÃO é persistido
no servidor: o banco só guarda o conteúdo fixo. Ver docs/API.md.
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


@router.get("", response_model=Pagina[NovenaItem], summary="Catálogo de novenas (US07)")
def listar_novenas(session: Sessao, paginacao: Paginacao,
                   santo_id: Annotated[int | None, Query(ge=1)] = None):
    return servico.listar(session, paginacao, santo_id)


@router.get("/{novena_id}", response_model=NovenaItem, summary="Detalhe de uma novena (US08)")
def detalhar_novena(session: Sessao, novena_id: IdNovena):
    return servico.detalhar(session, novena_id)


@router.get("/{novena_id}/dias", response_model=DiasDaNovena, summary="Os nove dias da novena (US08)")
def listar_dias(session: Sessao, novena_id: IdNovena):
    return servico.listar_dias(session, novena_id)


@router.get("/{novena_id}/dias/{numero_dia}", response_model=DiaNovenaDetalhe,
            summary="Conteúdo de um dia e navegação (US09, US10)")
def obter_dia(session: Sessao, novena_id: IdNovena,
              numero_dia: Annotated[int, Path(ge=1, le=DIAS_DA_NOVENA)]):
    return servico.obter_dia(session, novena_id, numero_dia)

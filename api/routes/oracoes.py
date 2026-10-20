"""US04, US05, US06: catálogo de orações, orações básicas e filtro por momento do dia."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import RESPOSTAS_ERRO
from ..schemas.comum import Pagina
from ..schemas.oracoes import MomentoItem, OracaoItem
from ..services import oracoes as servico
from ..services.paginacao import Paginacao

router = APIRouter(tags=["Orações"], responses=RESPOSTAS_ERRO)
Sessao = Annotated[Session, Depends(get_session)]


@router.get("/oracoes", response_model=Pagina[OracaoItem], summary="Lista orações com filtros combináveis (US04-US06)")
def listar_oracoes(
    session: Sessao, paginacao: Paginacao,
    basica: Annotated[bool | None, Query(description="true: só orações básicas; false: só as demais.")] = None,
    momento_id: Annotated[int | None, Query(ge=1, description="Id obtido em /momentos.")] = None,
    santo_id: Annotated[int | None, Query(ge=1, description="Só orações deste santo.")] = None,
):
    return servico.listar(session, paginacao, basica, momento_id, santo_id)


@router.get("/momentos", response_model=list[MomentoItem], summary="Momentos do dia cadastrados (US06)")
def listar_momentos(session: Sessao):
    return servico.listar_momentos(session)

"""US01, US02 e US03: catálogo, busca e detalhe de santos."""
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import RESPOSTAS_ERRO
from ..schemas.comum import Pagina
from ..schemas.santos import SantoDetalhe, SantoResumo
from ..services import santos as servico
from ..services.paginacao import Paginacao

router = APIRouter(prefix="/santos", tags=["Santos"], responses=RESPOSTAS_ERRO)
Sessao = Annotated[Session, Depends(get_session)]


@router.get("", response_model=Pagina[SantoResumo], summary="Lista/pesquisa santos (US01, US02)")
def listar_santos(
    session: Sessao, paginacao: Paginacao,
    q: Annotated[str | None, Query(max_length=100, description="Nome (parcial; ignora acento e caixa).")] = None,
):
    return servico.listar(session, paginacao, q)


@router.get("/{santo_id}", response_model=SantoDetalhe, summary="Detalhe de um santo (US03)")
def detalhar_santo(session: Sessao, santo_id: Annotated[int, Path(ge=1)]):
    return servico.detalhar(session, santo_id)

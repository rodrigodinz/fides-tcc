"""US11, US12, US13: catálogo, cards e detalhe de livros e textos importantes."""
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import RESPOSTAS_ERRO
from ..schemas.comum import Pagina
from ..schemas.livros import LivroDetalhe, LivroItem
from ..services import livros as servico
from ..services.paginacao import Paginacao

router = APIRouter(prefix="/livros", tags=["Livros"], responses=RESPOSTAS_ERRO)
Sessao = Annotated[Session, Depends(get_session)]


@router.get("", response_model=Pagina[LivroItem], summary="Catálogo de livros (US11, US12)")
def listar_livros(session: Sessao, paginacao: Paginacao,
                  santo_id: Annotated[int | None, Query(ge=1)] = None):
    return servico.listar(session, paginacao, santo_id)


@router.get("/{livro_id}", response_model=LivroDetalhe, summary="Detalhe: resumo e contexto histórico (US13)")
def detalhar_livro(session: Sessao, livro_id: Annotated[int, Path(ge=1)]):
    return servico.detalhar(session, livro_id)

"""US11, US12, US13 (UC12, UC13): catálogo, recomendação de leitura e detalhe de livros."""
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from pydantic import Field
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import RESPOSTAS_ERRO
from ..schemas.comum import Pagina
from ..schemas.livros import LivroDetalhe, LivroItem
from ..services import livros as servico
from ..services.paginacao import Paginacao

router = APIRouter(prefix="/livros", tags=["Livros"], responses=RESPOSTAS_ERRO)
Sessao = Annotated[Session, Depends(get_session)]
MAX_SANTOS_RECOMENDACAO = 20


@router.get("", response_model=Pagina[LivroItem], summary="Catálogo de livros")
def listar_livros(session: Sessao, paginacao: Paginacao,
                  santo_id: Annotated[int | None, Query(ge=1)] = None):
    return servico.listar(session, paginacao, santo_id)


# Declarada antes de /{livro_id}, senão "recomendados" seria lido como id.
@router.get("/recomendados", response_model=Pagina[LivroItem],
            summary="Recomendação de leitura")
def livros_recomendados(
    session: Sessao, paginacao: Paginacao,
    santo_id: Annotated[list[Annotated[int, Field(ge=1)]],
                        Query(min_length=1, max_length=MAX_SANTOS_RECOMENDACAO,
                              description="Ids dos santos acessados recentemente. Ex.:"
                                          "(?santo_id=4&santo_id=1).")],
):
    return servico.recomendados(session, paginacao, santo_id)


@router.get("/{livro_id}", response_model=LivroDetalhe, summary="Detalhe: resumo e contexto histórico")
def detalhar_livro(session: Sessao, livro_id: Annotated[int, Path(ge=1)]):
    return servico.detalhar(session, livro_id)

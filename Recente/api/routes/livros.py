from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from pydantic import Field
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import Respostas_De_Erro
from ..schemas.comum import Pagina
from ..schemas.livros import DetalhesDoLivro, ResumoDoLivro
from ..services import livros as servico
from ..services.paginacao import Paginacao

# APIRouter agrupa as rotas deste módulo: prefix entra antes de cada caminho, tags agrupa no /docs
# e responses documenta os erros padrão (400, 404, 422...) no OpenAPI
router = APIRouter(prefix="/livros", tags=["Livros"], responses=Respostas_De_Erro)
# Depends(get_session): o FastAPI abre uma sessão do banco por requisição e fecha no final
Sessao = Annotated[Session, Depends(get_session)]
max_recomendacao = 20  # no máximo 20 santos na recomendação


# GET /api/v1/livros -> Pagina[...] é o envelope de paginação com os itens dentro
@router.get("", response_model=Pagina[ResumoDoLivro], summary="Catálogo de livros")
def listar_livros(session: Sessao, paginacao: Paginacao,
                  santo_id: Annotated[int | None, Query(ge=1)] = None):
    return servico.listar_livros(session, paginacao, santo_id)


# precisa vir antes de /{livro_id}, senão "recomendados" seria lido como id
@router.get("/recomendados", response_model=Pagina[ResumoDoLivro],
            summary="Recomendação de leitura")
def livros_recomendados(
    session: Sessao, paginacao: Paginacao,
    santo_id: Annotated[list[Annotated[int, Field(ge=1)]],
                        Query(min_length=1, max_length=max_recomendacao,
                              description="Ids dos santos acessados recentemente. "
                                          "Ex.: ?santo_id=4&santo_id=1")],
):
    return servico.livros_recomendados(session, paginacao, santo_id)


# {livro_id} vem do caminho; Path(ge=1) recusa id zero ou negativo
@router.get("/{livro_id}", response_model=DetalhesDoLivro, summary="Detalhe: resumo e contexto histórico")
def detalhar_livro(session: Sessao, livro_id: Annotated[int, Path(ge=1)]):
    return servico.detalhar_coisas_livro(session, livro_id)

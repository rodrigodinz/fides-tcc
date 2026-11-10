from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import Respostas_De_Erro
from ..schemas.comum import Pagina
from ..schemas.santos import DetalhesDoSanto, ResumoDoSanto
from ..services import santos as servico
from ..services.paginacao import Paginacao

router = APIRouter(prefix="/santos", tags=["Santos"], responses=Respostas_De_Erro)
Sessao = Annotated[Session, Depends(get_session)]


# GET /api/v1/santos?nome=... → lista e busca na mesma rota
@router.get("", response_model=Pagina[ResumoDoSanto], summary="Lista e pesquisa santos")
def listar_santos(
    session: Sessao, paginacao: Paginacao,
    nome: Annotated[str | None, Query(max_length=100, description="Nome ou parte do nome do santo.")] = None,
):
    return servico.listar_santos(session, paginacao, nome)


# GET /api/v1/santos/{id} → santo com suas orações, novenas e livros
@router.get("/{santo_id}", response_model=DetalhesDoSanto, summary="Detalhes de um santo")
def detalhar_santo(session: Sessao, santo_id: Annotated[int, Path(ge=1)]):
    return servico.detalhar_santo(session, santo_id)

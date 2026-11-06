from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_session

from ..errors import Respostas_De_Erro
from ..schemas.comum import Pagina
from ..schemas.oracoes import ConteudoDaOracao, ConteudoDoMomento
from ..services import oracoes as servico
from ..services.paginacao import Paginacao

# sem prefix: este módulo tem duas rotas de raiz diferentes (/oracoes e /momentos)
router = APIRouter(tags=["Orações"], responses=Respostas_De_Erro)
# Depends(get_session): o FastAPI abre uma sessão do banco por requisição e fecha no final
Sessao = Annotated[Session, Depends(get_session)]


# GET /api/v1/oracoes -> os filtros são opcionais e podem ser combinados
@router.get("/oracoes", response_model=Pagina[ConteudoDaOracao], summary="Lista orações com filtros")
def listar_oracoes(
    session: Sessao, paginacao: Paginacao,
    basica: Annotated[bool | None, Query(description="true: só orações básicas; false: as demais.")] = None,
    momento_id: Annotated[int | None, Query(ge=1, description="Id obtido em /momentos.")] = None,
    santo_id: Annotated[int | None, Query(ge=1, description="Só as orações do santo.")] = None,
):
    return servico.listar_oracoes(session, paginacao, basica, momento_id, santo_id)


# GET /api/v1/momentos -> usado pelo front para montar os filtros por momento do dia
@router.get("/momentos", response_model=list[ConteudoDoMomento], summary="Momentos do dia cadastrados")
def listar_momentos_do_dia(session: Sessao):
    return servico.listar_momentos_do_dia(session)

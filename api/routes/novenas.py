from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from database.connection import get_session
from database.models import Dias_Da_Novena

from ..errors import Respostas_De_Erro
from ..schemas.comum import Pagina
from ..schemas.novenas import ConteudoNovena, DetalhesDoDiaDaNovena, DiasDaNovena
from ..services import novenas as servico
from ..services.paginacao import Paginacao

# APIRouter agrupa as rotas deste módulo: prefix entra antes de cada caminho, tags agrupa no /docs
# e responses documenta os erros padrão (400, 404, 422...) no OpenAPI
router = APIRouter(prefix="/novenas", tags=["Novenas"], responses=Respostas_De_Erro)
# Depends(get_session): o FastAPI abre uma sessão do banco por requisição e fecha no final
Sessao = Annotated[Session, Depends(get_session)]
IdNovena = Annotated[int, Path(ge=1)]  # id reaproveitado em todas as rotas abaixo


# GET /api/v1/novenas (cada item já traz a agenda, se houver)
@router.get("", response_model=Pagina[ConteudoNovena], summary="Catálogo de novenas com a agenda de cada uma")
def listar_novenas(session: Sessao, paginacao: Paginacao,
                   santo_id: Annotated[int | None, Query(ge=1)] = None):
    return servico.listar_novenas_com_agenda(session, paginacao, santo_id)


# GET /api/v1/novenas/{id}
@router.get("/{novena_id}", response_model=ConteudoNovena, summary="Detalhe e progresso da novena")
def detalhar_novena(session: Sessao, novena_id: IdNovena):
    return servico.detalhar_progresso_novena(session, novena_id)


# GET /api/v1/novenas/{id}/dias -> calendário com a data de cada dia
@router.get("/{novena_id}/dias", response_model=DiasDaNovena, summary="Calendário dos nove dias")
def listar_dias(session: Sessao, novena_id: IdNovena):
    return servico.listar_dias_novena(session, novena_id)


# GET /api/v1/novenas/{id}/dias/{n} -> reflexão e orações do dia (n de 1 a 9)
@router.get("/{novena_id}/dias/{numero_do_dia}", response_model=DetalhesDoDiaDaNovena,
            summary="Conteúdo do dia da novena")
def ver_conteudo_novena(session: Sessao, novena_id: IdNovena,
                        numero_do_dia: Annotated[int, Path(ge=1, le=Dias_Da_Novena)]):
    return servico.ver_dia_novena(session, novena_id, numero_do_dia)

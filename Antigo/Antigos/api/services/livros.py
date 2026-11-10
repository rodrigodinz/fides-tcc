from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database.models import Livro

from ..errors import nao_encontrado
from ..schemas.comum import Pagina, SantoRef
from ..schemas.livros import LivroDetalhe, LivroItem
from .paginacao import ParamsPaginacao, paginar


def _santo(l: Livro):
    return SantoRef(id=l.santo.id, nome=l.santo.nome) if l.santo else None


def _item(l: Livro) -> LivroItem:
    return LivroItem(id=l.id, titulo=l.titulo, autor=l.autor, santo=_santo(l))


def listar(session: Session, params: ParamsPaginacao, santo_id: int | None) -> Pagina[LivroItem]:
    consulta = select(Livro)
    if santo_id is not None:
        consulta = consulta.where(Livro.santo_id == santo_id)
    consulta = consulta.order_by(Livro.titulo, Livro.id)
    return paginar(session, consulta, params, _item, opcoes=(joinedload(Livro.santo),))


def detalhar(session: Session, livro_id: int) -> LivroDetalhe:
    livro = Livro.buscar_id(session, livro_id)  # método do modelo
    if livro is None:
        raise nao_encontrado("Livro")
    return LivroDetalhe(id=livro.id, titulo=livro.titulo, autor=livro.autor, santo=_santo(livro),
                        resumo=livro.resumo, contexto_historico=livro.contexto_historico)

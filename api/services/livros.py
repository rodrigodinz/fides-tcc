from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from database.models import Livro

from ..errors import erro_recurso_nao_encontrado
from ..schemas.comum import Pagina
from ..schemas.livros import DetalhesDoLivro, ResumoDoLivro
from .agenda import montar_referencia_do_santo
from .paginacao import ParametrosDePaginacao, paginar


def _montar_resumo_do_livro(livro: Livro) -> ResumoDoLivro:
    return ResumoDoLivro(id=livro.id, titulo=livro.titulo, autor=livro.autor,
                         santo=montar_referencia_do_santo(livro.santo))


def listar_livros(session: Session, parametros: ParametrosDePaginacao,
                  santo_id: int | None) -> Pagina[ResumoDoLivro]:
    consulta = select(Livro)
    if santo_id is not None:
        consulta = consulta.where(Livro.santo_id == santo_id)
    consulta = consulta.order_by(Livro.titulo, Livro.id)
    return paginar(session, consulta, parametros, _montar_resumo_do_livro,
                   opcoes_de_carregamento=(joinedload(Livro.santo),))


def livros_recomendados(session: Session, parametros: ParametrosDePaginacao,
                        ids_dos_santos: list[int]) -> Pagina[ResumoDoLivro]:
    consulta = (select(Livro).where(Livro.santo_id.in_(set(ids_dos_santos)))
                .order_by(Livro.titulo, Livro.id))
    return paginar(session, consulta, parametros, _montar_resumo_do_livro,
                   opcoes_de_carregamento=(joinedload(Livro.santo),))


def detalhar_coisas_livro(session: Session, livro_id: int) -> DetalhesDoLivro:
    livro = Livro.buscar_por_id(session, livro_id)
    if livro is None:
        raise erro_recurso_nao_encontrado("Livro")
    return DetalhesDoLivro(id=livro.id, titulo=livro.titulo, autor=livro.autor,
                           santo=montar_referencia_do_santo(livro.santo),
                           resumo=livro.resumo, contexto_historico=livro.contexto_historico)

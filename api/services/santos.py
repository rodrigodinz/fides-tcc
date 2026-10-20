from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Santo

from ..errors import nao_encontrado
from ..schemas.comum import Pagina
from ..schemas.santos import LivroDoSanto, NovenaDoSanto, OracaoDoSanto, SantoDetalhe, SantoResumo
from .busca import escapar_like, normalizar_busca
from .paginacao import ParamsPaginacao, pagina_vazia, paginar


def listar(session: Session, params: ParamsPaginacao, q: str | None) -> Pagina[SantoResumo]:
    consulta = select(Santo)
    if q is not None and q.strip():
        termo = normalizar_busca(q)
        if not termo:  # ex.: só ideogramas/símbolos: nada a casar (evita LIKE '%%')
            return pagina_vazia(params)
        consulta = consulta.where(Santo.nome_busca.like(f"%{escapar_like(termo)}%", escape="\\"))
    consulta = consulta.order_by(Santo.nome, Santo.id)
    return paginar(session, consulta, params, SantoResumo.model_validate)


def detalhar(session: Session, santo_id: int) -> SantoDetalhe:
    santo = Santo.buscar_id(session, santo_id)  # método do modelo
    if santo is None:
        raise nao_encontrado("Santo")
    # Os relacionamentos do ORM só trazem registros com id_santo == santo.id.
    return SantoDetalhe(
        id=santo.id, nome=santo.nome, foto_url=santo.foto_url, biografia=santo.biografia,
        oracoes=[OracaoDoSanto(id=o.id, titulo=o.titulo, basica=o.basica) for o in santo.obter_oracoes()],
        novenas=[NovenaDoSanto(id=n.id, titulo=n.titulo, descricao=n.descricao) for n in santo.obter_novena()],
        livros=[LivroDoSanto(id=l.id, titulo=l.titulo, autor=l.autor) for l in santo.obter_livro()],
    )

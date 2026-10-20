from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from database.models import MomentoDia, Oracao

from ..schemas.comum import Pagina, SantoRef
from ..schemas.oracoes import MomentoItem, OracaoItem
from .paginacao import ParamsPaginacao, paginar


def _momento(m: MomentoDia) -> MomentoItem:
    return MomentoItem(id=m.id, codigo=m.bloco.name.lower(), nome=m.bloco.value)


def _oracao(o: Oracao) -> OracaoItem:
    return OracaoItem(
        id=o.id, titulo=o.titulo, texto=o.texto, basica=o.basica,
        santo=SantoRef(id=o.santo.id, nome=o.santo.nome) if o.santo else None,
        momentos=[_momento(m) for m in sorted(o.momentos, key=lambda m: m.id)],
    )


def listar(session: Session, params: ParamsPaginacao, basica: bool | None,
           momento_id: int | None, santo_id: int | None) -> Pagina[OracaoItem]:
    consulta = select(Oracao)
    if basica is not None:
        consulta = consulta.where(Oracao.basica.is_(basica))
    if santo_id is not None:
        consulta = consulta.where(Oracao.santo_id == santo_id)
    if momento_id is not None:
        # N:N via Oracao_Momento_Dia; filtrando por UM id não há duplicatas de linha.
        consulta = consulta.join(Oracao.momentos).where(MomentoDia.id == momento_id)
    consulta = consulta.order_by(Oracao.titulo, Oracao.id)
    return paginar(session, consulta, params, _oracao,
                   opcoes=(joinedload(Oracao.santo), selectinload(Oracao.momentos)))


def listar_momentos(session: Session) -> list[MomentoItem]:
    return [_momento(m) for m in MomentoDia.listar_todos(session)]  # método do modelo

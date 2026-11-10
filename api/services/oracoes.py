from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from database.models import MomentoDia, Oracao

from ..schemas.comum import Pagina
from ..schemas.oracoes import ConteudoDaOracao, ConteudoDoMomento
from .agenda import montar_referencia_do_santo
from .paginacao import ParametrosDePaginacao, paginar


def _montar_momento(momento: MomentoDia) -> ConteudoDoMomento:
    return ConteudoDoMomento(id=momento.id, codigo=momento.bloco.name.lower(), nome=momento.bloco.value)


def _montar_oracao(oracao: Oracao) -> ConteudoDaOracao:
    return ConteudoDaOracao(
        id=oracao.id, titulo=oracao.titulo, texto=oracao.texto, basica=oracao.basica,
        santo=montar_referencia_do_santo(oracao.santo),
        momentos=[_montar_momento(momento) for momento in sorted(oracao.momentos, key=lambda momento: momento.id)],
    )


def listar_oracoes(session: Session, parametros: ParametrosDePaginacao, basica: bool | None,
                   momento_id: int | None, santo_id: int | None) -> Pagina[ConteudoDaOracao]:
    consulta = select(Oracao)
    if basica is not None:
        consulta = consulta.where(Oracao.basica.is_(basica))
    if santo_id is not None:
        consulta = consulta.where(Oracao.santo_id == santo_id)
    if momento_id is not None:
        consulta = consulta.join(Oracao.momentos).where(MomentoDia.id == momento_id)
    consulta = consulta.order_by(Oracao.titulo, Oracao.id)
    return paginar(session, consulta, parametros, _montar_oracao,
                   opcoes_de_carregamento=(joinedload(Oracao.santo), selectinload(Oracao.momentos)))


def listar_momentos_do_dia(session: Session) -> list[ConteudoDoMomento]:
    return [_montar_momento(momento) for momento in MomentoDia.listar_momentos_do_dia(session)]

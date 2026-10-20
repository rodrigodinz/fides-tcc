from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from database.models import DiaNovena, Novena

from ..errors import nao_encontrado
from ..schemas.comum import Pagina, SantoRef
from ..schemas.novenas import (DiaNovenaDetalhe, DiaResumo, DiasDaNovena, NovenaItem, NovenaRef,
                               OracaoBase)
from .paginacao import ParamsPaginacao, paginar


def _item(n: Novena) -> NovenaItem:
    return NovenaItem(id=n.id, titulo=n.titulo, descricao=n.descricao,
                      santo=SantoRef(id=n.santo.id, nome=n.santo.nome), total_dias=len(n.dias))


def listar(session: Session, params: ParamsPaginacao, santo_id: int | None) -> Pagina[NovenaItem]:
    consulta = select(Novena)
    if santo_id is not None:
        consulta = consulta.where(Novena.santo_id == santo_id)
    consulta = consulta.order_by(Novena.titulo, Novena.id)
    return paginar(session, consulta, params, _item,
                   opcoes=(joinedload(Novena.santo), selectinload(Novena.dias)))


def _obter(session: Session, novena_id: int) -> Novena:
    novena = Novena.buscar_id(session, novena_id)  # método do modelo
    if novena is None:
        raise nao_encontrado("Novena")
    return novena


def detalhar(session: Session, novena_id: int) -> NovenaItem:
    return _item(_obter(session, novena_id))


def listar_dias(session: Session, novena_id: int) -> DiasDaNovena:
    novena = _obter(session, novena_id)
    dias = novena.obter_dias()  # já ordenados por numero_dia
    return DiasDaNovena(novena=NovenaRef(id=novena.id, titulo=novena.titulo), total_dias=len(dias),
                        dias=[DiaResumo(id=d.id, numero_dia=d.numero_dia) for d in dias])


def obter_dia(session: Session, novena_id: int, numero_dia: int) -> DiaNovenaDetalhe:
    novena = _obter(session, novena_id)
    dia = DiaNovena.buscar_novena_dia(session, novena_id, numero_dia)  # método do modelo
    if dia is None:  # só ocorreria se o banco tivesse menos de 9 dias (o seed garante 9)
        raise nao_encontrado("Dia da novena")
    total = len(novena.dias)
    return DiaNovenaDetalhe(
        novena=NovenaRef(id=novena.id, titulo=novena.titulo),
        numero_dia=dia.numero_dia, total_dias=total, texto_reflexao=dia.texto_reflexao,
        # Ordem por id = ordem de cadastro (orações-base primeiro, depois as do santo).
        oracoes=[OracaoBase(id=o.id, titulo=o.titulo, texto=o.texto)
                 for o in sorted(dia.oracoes_base(), key=lambda o: o.id)],
        dia_anterior=dia.numero_dia - 1 if dia.numero_dia > 1 else None,
        proximo_dia=dia.numero_dia + 1 if dia.numero_dia < total else None,
    )

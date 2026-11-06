"""Paginação feita no SQL (COUNT + LIMIT/OFFSET), nunca em memória (RNF02)."""
from dataclasses import dataclass
from math import ceil
from typing import Annotated, Callable

from fastapi import Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from database.models import LIMITE_MAXIMO_POR_PAGINA

from ..schemas.comum import Pagina

PAGINA_MAXIMA = 1_000_000  # evita OFFSET astronômico (estouro de inteiro no SQLite)


@dataclass(frozen=True)
class ParamsPaginacao:
    pagina: int
    limite: int


def params_paginacao(
    pagina: Annotated[int, Query(ge=1, le=PAGINA_MAXIMA, description="Página (começa em 1).")] = 1,
    limite: Annotated[int, Query(ge=1, le=LIMITE_MAXIMO_POR_PAGINA,
                                 description="Itens por página (1 a 20).")] = LIMITE_MAXIMO_POR_PAGINA,
) -> ParamsPaginacao:
    return ParamsPaginacao(pagina, limite)


Paginacao = Annotated[ParamsPaginacao, Depends(params_paginacao)]


def paginar(session: Session, consulta: Select, params: ParamsPaginacao,
            converter: Callable, opcoes: tuple = ()) -> Pagina:
    """``consulta`` já traz filtros e ORDER BY; ``opcoes`` são loaders (só na consulta dos itens).

    A contagem usa exatamente os mesmos filtros da listagem.
    """
    total = session.scalar(select(func.count()).select_from(consulta.order_by(None).subquery())) or 0
    itens = session.scalars(
        consulta.options(*opcoes).limit(params.limite).offset((params.pagina - 1) * params.limite)
    ).all()
    return Pagina(itens=[converter(i) for i in itens], pagina=params.pagina, limite=params.limite,
                  total=total, total_paginas=ceil(total / params.limite))


def pagina_vazia(params: ParamsPaginacao) -> Pagina:
    return Pagina(itens=[], pagina=params.pagina, limite=params.limite, total=0, total_paginas=0)

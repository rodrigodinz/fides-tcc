from dataclasses import dataclass
from math import ceil
from typing import Annotated, Callable

from fastapi import Depends, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from database.models import Limite_Maximo_Por_Pagina

from ..schemas.comum import Pagina

Pagina_Maxima = 1_000_000


@dataclass(frozen=True)
class ParametrosDePaginacao:
    pagina: int
    limite: int


def ler_parametros_de_paginacao(
    pagina: Annotated[int, Query(ge=1, le=Pagina_Maxima, description="Página (começa em 1).")] = 1,
    limite: Annotated[int, Query(ge=1, le=Limite_Maximo_Por_Pagina,
                                 description="Itens por página (no máximo 20).")] = Limite_Maximo_Por_Pagina,
) -> ParametrosDePaginacao:
    return ParametrosDePaginacao(pagina, limite)


Paginacao = Annotated[ParametrosDePaginacao, Depends(ler_parametros_de_paginacao)]


# a paginação é feita no SQL (COUNT + LIMIT/OFFSET), nunca carregando tudo na memória
def paginar(session: Session, consulta: Select, parametros: ParametrosDePaginacao,
            converter_item: Callable, opcoes_de_carregamento: tuple = ()) -> Pagina:
    total_registros = session.scalar(
        select(func.count()).select_from(consulta.order_by(None).subquery())) or 0
    registros = session.scalars(
        consulta.options(*opcoes_de_carregamento)
        .limit(parametros.limite).offset((parametros.pagina - 1) * parametros.limite)
    ).all()
    return Pagina(itens=[converter_item(registro) for registro in registros],
                  pagina=parametros.pagina, limite=parametros.limite,
                  total_registros_filtros=total_registros,
                  total_paginas=ceil(total_registros / parametros.limite))


def montar_pagina_vazia(parametros: ParametrosDePaginacao) -> Pagina:
    return Pagina(itens=[], pagina=parametros.pagina, limite=parametros.limite,
                  total_registros_filtros=0, total_paginas=0)

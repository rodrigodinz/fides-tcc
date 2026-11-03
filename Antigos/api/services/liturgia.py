"""Liturgia (MVP): apenas dados de DEMONSTRAÇÃO vindos dos seeds.

A janela de ±7 dias é a do modelo: ``LiturgiaDia.buscar_data`` e
``LiturgiaHora.buscar_data`` lançam ``ForaDoIntervaloError`` (tratada em
api/errors.py como 400). A API não tem regra de intervalo própria; o campo
``intervalo`` da resposta usa a mesma constante e a mesma data de referência
(``date.today()``) do modelo.
"""
import logging
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from database.models import INTERVALO_LITURGIA_DIAS, BlocoLiturgia, LiturgiaDia, LiturgiaHora

from ..errors import ApiError
from ..schemas.liturgia import (BlocoRef, HoraItem, IntervaloLiturgia, LiturgiaDiaResposta,
                                LiturgiaHorasResposta)

logger = logging.getLogger("fides.api")

# REMOVER/SUBSTITUIR NA FASE 2, quando houver fonte oficial de liturgia aprovada.
AVISO_DEMONSTRACAO = ("Conteúdo de demonstração: estes textos não correspondem à liturgia oficial. "
                      "Serão substituídos por fonte oficial em versão futura.")

ORDEM_CANONICA = {bloco: i for i, bloco in enumerate(BlocoLiturgia)}  # Laudes, Horas médias, Vésperas


def _intervalo() -> IntervaloLiturgia:
    hoje = date.today()
    delta = timedelta(days=INTERVALO_LITURGIA_DIAS)
    return IntervaloLiturgia(hoje=hoje, inicio=hoje - delta, fim=hoje + delta)


def _sem_registro(data: date) -> ApiError:
    return ApiError(404, "LITURGIA_NAO_CADASTRADA",
                    f"Não há liturgia cadastrada para {data.isoformat()}, embora a data esteja "
                    "dentro do intervalo de consulta.")


def consultar_horas(session: Session, data: date | None, bloco: BlocoLiturgia | None) -> LiturgiaHorasResposta:
    data = data or date.today()
    registros = LiturgiaHora.buscar_data(session, data)  # valida a janela (ForaDoIntervaloError)

    por_bloco = defaultdict(list)
    for r in registros:
        por_bloco[r.bloco].append(r)

    avisos = []
    escolhidos = []
    for b, lista in por_bloco.items():
        lista.sort(key=lambda r: r.id)
        if len(lista) > 1:  # o banco admite; não esconder: registrar e sinalizar na resposta
            logger.warning("Integridade: %d registros de LiturgiaHora (%s) em %s; usando o id %d.",
                           len(lista), b.name, data, lista[0].id)
            avisos.append(f"Há {len(lista)} registros para '{b.value}' nesta data; "
                          "exibindo o primeiro cadastrado.")
        escolhidos.append(lista[0])

    if bloco is not None:
        escolhidos = [r for r in escolhidos if r.bloco == bloco]
    if not escolhidos:
        raise _sem_registro(data)

    escolhidos.sort(key=lambda r: ORDEM_CANONICA[r.bloco])
    return LiturgiaHorasResposta(
        data=data, intervalo=_intervalo(), aviso=AVISO_DEMONSTRACAO,
        avisos_integridade=avisos if bloco is None or any(bloco.value in a for a in avisos) else [],
        horas=[HoraItem(bloco=BlocoRef(codigo=r.bloco.name.lower(), nome=r.bloco.value), texto=r.texto)
               for r in escolhidos],
    )


def consultar_dia(session: Session, data: date | None) -> LiturgiaDiaResposta:
    data = data or date.today()
    dia = LiturgiaDia.buscar_data(session, data)  # valida a janela (ForaDoIntervaloError)
    if dia is None:
        raise _sem_registro(data)
    return LiturgiaDiaResposta(
        data=data, intervalo=_intervalo(), aviso=AVISO_DEMONSTRACAO,
        santo_celebrado=dia.santo_celebrado, primeira_leitura=dia.primeira_leitura,
        salmo=dia.salmo, evangelho=dia.evangelho,
        # segunda leitura: apenas o que está cadastrado, sem inventar nada
        segunda_leitura=dia.segunda_leitura if dia.possui_segunda_leitura() else None,
        possui_segunda_leitura=dia.possui_segunda_leitura(),
    )

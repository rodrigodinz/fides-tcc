"""Liturgia (MVP): apenas dados de DEMONSTRAÇÃO vindos dos seeds.

A janela de ±7 dias é a do modelo: ``LiturgiaDia.buscar_data``,
``LiturgiaHora.buscar_data`` e ``LiturgiaHora.buscar_bloco`` chamam
``Agenda._validar_intervalo`` e lançam ``ForaDoIntervaloError`` (tratada em
api/errors.py como 400). Os mesmos métodos já ocultam registros de agendas de
liturgia canceladas. A API não tem regra de intervalo própria; o campo
``intervalo`` usa a mesma constante e a mesma data de referência
(``date.today()``) do modelo.

O banco garante um único registro de Liturgia das Horas por (data, bloco)
(``uq_liturgia_hora_data_bloco``), por isso não há tratamento de duplicidade.
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from database.models import INTERVALO_LITURGIA_DIAS, BlocoLiturgia, LiturgiaDia, LiturgiaHora

from ..errors import ApiError
from ..schemas.liturgia import (BlocoRef, HoraItem, IntervaloLiturgia, LeiturasDoDia,
                                LiturgiaDiaResposta, LiturgiaHorasResposta)

# Remover esse texto na Fase 2 do projeto
AVISO_DEMONSTRACAO = ("Conteúdo de demonstração: estes textos não correspondem à liturgia oficial. "
                      "Serão substituídos por fonte oficial na Fase 2 do Fides.")

ORDEM_CANONICA = {bloco: i for i, bloco in enumerate(BlocoLiturgia)}  # Laudes, Horas médias, Vésperas


def intervalo() -> IntervaloLiturgia:
    hoje = date.today()
    delta = timedelta(days=INTERVALO_LITURGIA_DIAS)
    return IntervaloLiturgia(hoje=hoje, inicio=hoje - delta, fim=hoje + delta)


def _sem_registro(data: date) -> ApiError:
    return ApiError(404, "LITURGIA_NAO_CADASTRADA",
                    f"Não há liturgia cadastrada para {data.isoformat()}.")


def leituras(dia: LiturgiaDia) -> LeiturasDoDia:
    return LeiturasDoDia(
        santo_celebrado=dia.santo_celebrado, primeira_leitura=dia.primeira_leitura,
        salmo=dia.salmo, evangelho=dia.evangelho,
        segunda_leitura=dia.segunda_leitura if dia.possui_segunda_leitura() else None,
        possui_segunda_leitura=dia.possui_segunda_leitura())


def horas_em_ordem(registros) -> list[HoraItem]:
    """Blocos na ordem canônica (Laudes, Horas médias, Vésperas)."""
    return [HoraItem(bloco=BlocoRef(codigo=r.bloco.name.lower(), nome=r.bloco.value), texto=r.texto)
            for r in sorted(registros, key=lambda r: ORDEM_CANONICA[r.bloco])]


def consultar_horas(session: Session, data: date | None, bloco: BlocoLiturgia | None) -> LiturgiaHorasResposta:
    data = data or date.today()
    if bloco is None:
        registros = LiturgiaHora.buscar_data(session, data)  # valida a janela
    else:
        registro = LiturgiaHora.buscar_bloco(session, data, bloco)  # valida a janela
        registros = [registro] if registro is not None else []
    if not registros:
        raise _sem_registro(data)
    return LiturgiaHorasResposta(data=data, intervalo=intervalo(), aviso=AVISO_DEMONSTRACAO,
                                 horas=horas_em_ordem(registros))


def consultar_dia(session: Session, data: date | None) -> LiturgiaDiaResposta:
    data = data or date.today()
    dia = LiturgiaDia.buscar_data(session, data)  # valida a janela
    if dia is None:
        raise _sem_registro(data)
    return LiturgiaDiaResposta(data=data, intervalo=intervalo(), aviso=AVISO_DEMONSTRACAO,
                               **leituras(dia).model_dump())

"""Agenda do dia (UC08, UC14, UC15, UC16): conteúdo que a agenda reserva para uma data.

A janela de ±7 dias é validada pelo próprio modelo: ``LiturgiaDia.buscar_data``
lança ``ForaDoIntervaloError`` (400) antes de qualquer outra consulta. Dentro da
janela, a ausência de liturgia não é erro aqui: a agenda do dia apenas informa
``liturgia_dia: null`` / ``liturgia_horas: []``.
"""
from datetime import date

from sqlalchemy.orm import Session

from database.models import LiturgiaDia, LiturgiaHora

from ..schemas.agenda import AgendaDoDia
from .agenda import novenas_em_andamento
from .liturgia import AVISO_DEMONSTRACAO, horas_em_ordem, intervalo, leituras


def consultar(session: Session, data: date | None) -> AgendaDoDia:
    data = data or date.today()
    dia = LiturgiaDia.buscar_data(session, data)  # valida a janela (ForaDoIntervaloError -> 400)
    horas = LiturgiaHora.buscar_data(session, data)
    return AgendaDoDia(
        data=data, intervalo=intervalo(), aviso=AVISO_DEMONSTRACAO,
        liturgia_dia=leituras(dia) if dia is not None else None,
        liturgia_horas=horas_em_ordem(horas),
        novenas_em_andamento=novenas_em_andamento(session, data),
    )

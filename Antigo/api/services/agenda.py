"""Leitura da Agenda: progresso global das novenas e conteúdo de cada dia.

Todas as regras vêm do modelo (``database/models.py``):
  * ``Agenda.buscar_ativa``    -> agenda ATIVA em andamento ou futura de uma novena;
  * ``Agenda.listar_ativas``   -> agendas ATIVAS (em andamento ou futuras) de um tipo;
  * ``Agenda.calcular_dia_atual`` -> "Dia X de 9" (1-9) ou 0 fora do período.
A API não recalcula período, status nem janela de liturgia.
"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from database.models import Agenda, Novena, TipoAgenda

from ..schemas.agenda import AgendaNovena, NovenaEmAndamento, NovenaNaAgenda
from ..schemas.comum import SantoRef


def santo_ref(santo) -> SantoRef | None:
    return SantoRef(id=santo.id, nome=santo.nome) if santo is not None else None


def agenda_da_novena(session: Session, novena: Novena, hoje: date | None = None) -> AgendaNovena | None:
    agenda = Agenda.buscar_ativa(session, novena.id, hoje=hoje)
    if agenda is None:
        return None
    dia = agenda.calcular_dia_atual(hoje=hoje)
    return AgendaNovena(id=agenda.id, data_inicio=agenda.data_inicio, data_fim=agenda.data_fim,
                        dia_atual=dia, situacao="em_andamento" if dia >= 1 else "agendada")


def data_do_dia(agenda: AgendaNovena | None, numero_dia: int) -> date | None:
    """Data do calendário correspondente ao dia N (dia 1 = data de início da agenda)."""
    return agenda.data_inicio + timedelta(days=numero_dia - 1) if agenda else None


def novenas_em_andamento(session: Session, data: date) -> list[NovenaEmAndamento]:
    """Novenas que o período tem a data ativa, tipo, que ja comecou (dia 1 a 9 nessa data)."""
    resultado = []
    for agenda in Agenda.listar_ativas(session, TipoAgenda.NOVENA, hoje=data):
        dia = agenda.calcular_dia_atual(hoje=data)
        if dia < 1 or agenda.novena is None:
            continue  # ainda não começou nessa data
        novena = agenda.novena
        resultado.append(NovenaEmAndamento(
            novena=NovenaNaAgenda(id=novena.id, titulo=novena.titulo, santo=santo_ref(novena.santo)),
            agenda_id=agenda.id, data_inicio=agenda.data_inicio, data_fim=agenda.data_fim,
            dia_atual=dia, total_dias=len(novena.dias)))
    return resultado

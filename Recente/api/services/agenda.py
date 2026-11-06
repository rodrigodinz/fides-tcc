from datetime import date, timedelta

from sqlalchemy.orm import Session

from database.models import Agenda, Novena, TipoAgenda

from ..schemas.agenda import AgendaDaNovena, NovenaEmAndamento, NovenaNaAgenda
from ..schemas.comum import ReferenciaDoSanto


def montar_referencia_do_santo(santo) -> ReferenciaDoSanto | None:
    return ReferenciaDoSanto(id=santo.id, nome=santo.nome) if santo is not None else None


def buscar_agenda_da_novena(session: Session, novena: Novena, hoje: date | None = None) -> AgendaDaNovena | None:
    agenda = Agenda.buscar_agenda_ativa_da_novena(session, novena.id, hoje=hoje)
    if agenda is None:
        return None
    dia_atual = agenda.calcular_dia_atual(hoje=hoje)
    return AgendaDaNovena(id=agenda.id, data_inicio=agenda.data_inicio, data_fim=agenda.data_fim,
                          dia_atual=dia_atual, situacao="em_andamento" if dia_atual >= 1 else "agendada")


def calcular_data_do_dia(agenda: AgendaDaNovena | None, numero_do_dia: int) -> date | None:
    return agenda.data_inicio + timedelta(days=numero_do_dia - 1) if agenda else None


# Novenas que o período tem a data ativa, tipo, que ja comecou (dia 1 a 9 nessa data).
def listar_novenas_em_andamento(session: Session, data: date) -> list[NovenaEmAndamento]:
    novenas_em_andamento = []
    for agenda in Agenda.listar_agendas_ativas(session, TipoAgenda.NOVENA, hoje=data):
        dia_atual = agenda.calcular_dia_atual(hoje=data)
        if dia_atual < 1 or agenda.novena is None:
            continue
        novena = agenda.novena
        novenas_em_andamento.append(NovenaEmAndamento(
            novena=NovenaNaAgenda(id=novena.id, titulo=novena.titulo,
                                  santo=montar_referencia_do_santo(novena.santo)),
            agenda_id=agenda.id, data_inicio=agenda.data_inicio, data_fim=agenda.data_fim,
            dia_atual=dia_atual, total_dias=len(novena.dias)))
    return novenas_em_andamento

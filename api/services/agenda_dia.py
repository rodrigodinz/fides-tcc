from datetime import date

from sqlalchemy.orm import Session

from database.models import LiturgiaDia, LiturgiaHora

from ..schemas.agenda import ConteudosDoDia
from .agenda import listar_novenas_em_andamento
from .liturgia import Aviso_Demonstracao, montar_leituras_do_dia, ordenar_horas_da_liturgia, periodo_da_liturgia


def consultar_conteudos_do_dia(session: Session, data: date | None) -> ConteudosDoDia:
    data = data or date.today()
    liturgia_do_dia = LiturgiaDia.buscar_por_data(session, data)
    liturgia_das_horas = LiturgiaHora.buscar_por_data(session, data)
    return ConteudosDoDia(
        data=data, periodo=periodo_da_liturgia(),
        liturgia_do_dia=montar_leituras_do_dia(liturgia_do_dia) if liturgia_do_dia is not None else None,
        liturgia_das_horas=ordenar_horas_da_liturgia(liturgia_das_horas),
        novenas_em_andamento=listar_novenas_em_andamento(session, data),
        aviso=Aviso_Demonstracao,
    )

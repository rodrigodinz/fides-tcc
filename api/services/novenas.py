from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from database.models import Conteudo_Dia_Novena, Novena

from ..errors import erro_recurso_nao_encontrado
from ..schemas.comum import Pagina
from ..schemas.novenas import (ConteudoNovena, DetalhesDoDiaDaNovena, DiasDaNovena, OracaoBaseDoDia,
                               ReferenciaDaNovena, ResumoDoDiaDaNovena)
from .agenda import buscar_agenda_da_novena, calcular_data_do_dia, montar_referencia_do_santo
from .paginacao import ParametrosDePaginacao, paginar


def _montar_conteudo_da_novena(session: Session, novena: Novena) -> ConteudoNovena:
    return ConteudoNovena(id=novena.id, titulo=novena.titulo, descricao=novena.descricao,
                          santo=montar_referencia_do_santo(novena.santo), total_dias=len(novena.dias),
                          agenda=buscar_agenda_da_novena(session, novena))


def listar_novenas_com_agenda(session: Session, parametros: ParametrosDePaginacao,
                              santo_id: int | None) -> Pagina[ConteudoNovena]:
    consulta = select(Novena)
    if santo_id is not None:
        consulta = consulta.where(Novena.santo_id == santo_id)
    consulta = consulta.order_by(Novena.titulo, Novena.id)
    return paginar(session, consulta, parametros, lambda novena: _montar_conteudo_da_novena(session, novena),
                   opcoes_de_carregamento=(joinedload(Novena.santo), selectinload(Novena.dias)))


def _buscar_novena_ou_erro(session: Session, novena_id: int) -> Novena:
    novena = Novena.buscar_por_id(session, novena_id)
    if novena is None:
        raise erro_recurso_nao_encontrado("Novena")
    return novena


def detalhar_progresso_novena(session: Session, novena_id: int) -> ConteudoNovena:
    return _montar_conteudo_da_novena(session, _buscar_novena_ou_erro(session, novena_id))


def listar_dias_novena(session: Session, novena_id: int) -> DiasDaNovena:
    novena = _buscar_novena_ou_erro(session, novena_id)
    agenda = buscar_agenda_da_novena(session, novena)
    dias = novena.ver_dias_da_novena()
    return DiasDaNovena(
        novena=ReferenciaDaNovena(id=novena.id, titulo=novena.titulo), total_dias=len(dias), agenda=agenda,
        dias=[ResumoDoDiaDaNovena(id=dia.id, numero_do_dia=dia.numero_do_dia,
                                  data=calcular_data_do_dia(agenda, dia.numero_do_dia))
              for dia in dias])


def ver_dia_novena(session: Session, novena_id: int, numero_do_dia: int) -> DetalhesDoDiaDaNovena:
    novena = _buscar_novena_ou_erro(session, novena_id)
    dia = Conteudo_Dia_Novena.buscar_dia_da_novena(session, novena_id, numero_do_dia)
    if dia is None:
        raise erro_recurso_nao_encontrado("Dia da novena")
    total_dias = len(novena.dias)
    agenda = buscar_agenda_da_novena(session, novena)
    return DetalhesDoDiaDaNovena(
        novena=ReferenciaDaNovena(id=novena.id, titulo=novena.titulo),
        numero_do_dia=dia.numero_do_dia, total_dias=total_dias,
        data=calcular_data_do_dia(agenda, dia.numero_do_dia),
        dia_atual=agenda.dia_atual if agenda else None,
        texto_reflexao=dia.texto_reflexao,
        oracoes=[OracaoBaseDoDia(id=oracao.id, titulo=oracao.titulo, texto=oracao.texto)
                 for oracao in sorted(dia.ver_oracoes_base(), key=lambda oracao: oracao.id)],
        dia_anterior=dia.numero_do_dia - 1 if dia.numero_do_dia > 1 else None,
        proximo_dia=dia.numero_do_dia + 1 if dia.numero_do_dia < total_dias else None,
    )

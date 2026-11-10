from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from .comum import ReferenciaDoSanto
from .liturgia import HoraDaLiturgia, LeiturasDoDia, PeriodoDaLiturgia

SituacaoDaNovena = Literal["em_andamento", "agendada"]  # Literal: só aceita esses dois textos


# progresso global da novena → é igual para todos os usuários
class AgendaDaNovena(BaseModel):
    id: int
    data_inicio: date = Field(description="Data do dia 1 da novena.")
    data_fim: date = Field(description="Data do dia 9 da novena (início + 8 dias).")
    dia_atual: int = Field(description="1 a 9 durante a novena; 0 se ainda não começou.")
    situacao: SituacaoDaNovena = Field(description="em_andamento (dia 1 a 9 hoje) ou agendada (começa depois).")


class NovenaNaAgenda(BaseModel):
    id: int
    titulo: str
    santo: ReferenciaDoSanto | None = None


class NovenaEmAndamento(BaseModel):
    novena: NovenaNaAgenda
    agenda_id: int
    data_inicio: date
    data_fim: date
    dia_atual: int = Field(description="Dia da novena na data consultada (1 a 9).")
    total_dias: int


# tudo o que a agenda reserva para uma data (liturgia + novenas em andamento)
class ConteudosDoDia(BaseModel):
    data: date
    periodo: PeriodoDaLiturgia
    liturgia_do_dia: LeiturasDoDia | None = Field(
        default=None, description="Leituras da Liturgia do Dia.")
    liturgia_das_horas: list[HoraDaLiturgia] = Field(
        default=[], description="Liturgia das Horas em ordem canônica.")
    novenas_em_andamento: list[NovenaEmAndamento] = Field(
        default=[], description="Novenas cujo período agendado inclui a data consultada.")
    aviso: str

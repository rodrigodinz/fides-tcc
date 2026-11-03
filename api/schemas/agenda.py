"""Schemas da Agenda (UC05, UC06, UC08, UC14).

A Agenda é definida pelo administrador (no MVP, pelos seeds) e controla o
conteúdo de cada dia: a liturgia daquela data e as novenas em andamento.
O "Dia X de 9" é derivado da agenda (``Agenda.calcular_dia_atual``), não é
progresso individual do fiel.
"""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from .comum import SantoRef
from .liturgia import HoraItem, IntervaloLiturgia, LeiturasDoDia

SituacaoNovena = Literal["em_andamento", "agendada"]


class AgendaNovena(BaseModel):
    id: int
    data_inicio: date = Field(description="Data do dia 1 da novena.")
    data_fim: date = Field(description="Data do dia 9 (início + 8 dias).")
    dia_atual: int = Field(description="1 a 9 durante a novena; 0 se ainda não começou.")
    situacao: SituacaoNovena = Field(description="em_andamento (dia 1-9 hoje) ou agendada (começa depois).")


class NovenaNaAgenda(BaseModel):
    id: int
    titulo: str
    santo: SantoRef | None = None


class NovenaEmAndamento(BaseModel):
    novena: NovenaNaAgenda
    agenda_id: int
    data_inicio: date
    data_fim: date
    dia_atual: int = Field(description="Dia da novena na data consultada (1 a 9).")
    total_dias: int


class AgendaDoDia(BaseModel):
    """Tudo o que a agenda reserva para uma data: liturgia e novenas em andamento."""

    data: date
    intervalo: IntervaloLiturgia
    liturgia_dia: LeiturasDoDia | None = Field(
        default=None, description="Liturgia do Dia da data; null se não houver registro.")
    liturgia_horas: list[HoraItem] = Field(
        default=[], description="Blocos da Liturgia das Horas em ordem canônica; vazio se não houver registro.")
    novenas_em_andamento: list[NovenaEmAndamento] = Field(
        default=[], description="Novenas cujo período agendado contém a data.")
    aviso: str

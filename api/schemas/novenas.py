from datetime import date

from pydantic import BaseModel, Field

from .agenda import AgendaDaNovena
from .comum import ReferenciaDoSanto


# usado na listagem e no detalhe da novena
class ConteudoNovena(BaseModel):
    id: int
    titulo: str
    descricao: str | None = None
    santo: ReferenciaDoSanto | None = None  # opcional, segundo a alexandra K
    total_dias: int
    agenda: AgendaDaNovena | None = Field(
        default=None, description="Agenda ativa (em andamento ou futura); null se a novena não estiver agendada.")


class ResumoDoDiaDaNovena(BaseModel):
    id: int
    numero_do_dia: int
    data: date | None = Field(default=None, description="Data do calendário deste dia, se a novena estiver agendada.")


class ReferenciaDaNovena(BaseModel):
    id: int
    titulo: str


class DiasDaNovena(BaseModel):
    novena: ReferenciaDaNovena
    total_dias: int
    agenda: AgendaDaNovena | None = None
    dias: list[ResumoDoDiaDaNovena]


class OracaoBaseDoDia(BaseModel):
    id: int
    titulo: str
    texto: str


# conteúdo de um dia e números do dia anterior e do próximo
class DetalhesDoDiaDaNovena(BaseModel):
    novena: ReferenciaDaNovena
    numero_do_dia: int
    total_dias: int
    data: date | None = Field(default=None, description="Data do calendário deste dia, se a novena estiver agendada.")
    dia_atual: int | None = Field(default=None, description="Dia atual da novena pela agenda (0 a 9); null se não agendada.")
    texto_reflexao: str
    oracoes: list[OracaoBaseDoDia]
    dia_anterior: int | None = Field(default=None, description="Null no primeiro dia.")  # nulo no primeiro dia
    proximo_dia: int | None = Field(default=None, description="Null no último dia.")  # nulo no último dia

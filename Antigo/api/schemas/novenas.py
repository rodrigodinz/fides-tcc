from datetime import date

from pydantic import BaseModel, Field

from .agenda import AgendaNovena
from .comum import SantoRef


class NovenaItem(BaseModel):
    id: int
    titulo: str
    descricao: str | None = None
    santo: SantoRef | None = None  # opcional, segundo a alexandra K
    total_dias: int
    agenda: AgendaNovena | None = Field(
        default=None, description="Agenda ativa (em andamento ou futura); null se a novena não estiver ativa.")


class DiaResumo(BaseModel):
    id: int
    numero_dia: int
    data: date | None = Field(default=None, description="Data do calendário deste dia, se a novena estiver ativa.")


class NovenaRef(BaseModel):
    id: int
    titulo: str


class DiasDaNovena(BaseModel):
    novena: NovenaRef
    total_dias: int
    agenda: AgendaNovena | None = None
    dias: list[DiaResumo]


class OracaoBase(BaseModel):
    id: int
    titulo: str
    texto: str


class DiaNovenaDetalhe(BaseModel):
    novena: NovenaRef
    numero_dia: int
    total_dias: int
    data: date | None = Field(default=None, description="Data do calendário deste dia, se a novena estiver ativa.")
    dia_atual: int | None = Field(default=None, description="Dia atual da novena pela agenda (0-9); null se não ativa.")
    texto_reflexao: str
    oracoes: list[OracaoBase]
    dia_anterior: int | None = None  # nulo no primeiro dia
    proximo_dia: int | None = None   # nulo no último dia

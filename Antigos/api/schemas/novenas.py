from pydantic import BaseModel

from .comum import SantoRef


class NovenaItem(BaseModel):
    id: int
    titulo: str
    descricao: str | None = None
    santo: SantoRef
    total_dias: int


class DiaResumo(BaseModel):
    id: int
    numero_dia: int


class NovenaRef(BaseModel):
    id: int
    titulo: str


class DiasDaNovena(BaseModel):
    novena: NovenaRef
    total_dias: int
    dias: list[DiaResumo]


class OracaoBase(BaseModel):
    id: int
    titulo: str
    texto: str


class DiaNovenaDetalhe(BaseModel):
    novena: NovenaRef
    numero_dia: int
    total_dias: int
    texto_reflexao: str
    oracoes: list[OracaoBase]
    dia_anterior: int | None = None  # nulo no primeiro dia
    proximo_dia: int | None = None   # nulo no último dia

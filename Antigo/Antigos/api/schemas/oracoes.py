from pydantic import BaseModel

from .comum import SantoRef


class MomentoItem(BaseModel):
    id: int
    codigo: str  # ex.: ao_acordar (derivado do enum BlocoMomento)
    nome: str    # ex.: "Ao acordar"


class OracaoItem(BaseModel):
    id: int
    titulo: str
    texto: str
    basica: bool
    santo: SantoRef | None = None  # nulo nas orações gerais (ex.: Pai Nosso)
    momentos: list[MomentoItem]

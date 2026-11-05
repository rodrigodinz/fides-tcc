from pydantic import BaseModel

from .comum import SantoRef


class MomentoItem(BaseModel):
    id: int
    codigo: str  # tipo, ao acordar
    nome: str    # tipo, "Ao acordar"


class OracaoItem(BaseModel):
    id: int
    titulo: str
    texto: str
    basica: bool
    santo: SantoRef | None = None  #Nulo nas oracoes gerais, tipo pai nosso
    momentos: list[MomentoItem]

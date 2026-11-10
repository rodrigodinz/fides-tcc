from pydantic import BaseModel

from .comum import SantoRef


class LivroItem(BaseModel):
    id: int
    titulo: str
    autor: str
    santo: SantoRef | None = None  # nulo em livros que nao tem um santo


class LivroDetalhe(LivroItem):
    resumo: str | None = None
    contexto_historico: str | None = None

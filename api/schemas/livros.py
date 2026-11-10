from pydantic import BaseModel, Field

from .comum import ReferenciaDoSanto


class ResumoDoLivro(BaseModel):
    id: int
    titulo: str
    autor: str
    santo: ReferenciaDoSanto | None = Field(default=None, description="Null nos livros que não têm santo.")  # nulo em livros que nao tem um santo


# detalhe → resumo do livro, resumo do conteúdo e contexto histórico
class DetalhesDoLivro(ResumoDoLivro):
    resumo: str | None = None
    contexto_historico: str | None = None

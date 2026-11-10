from typing import Generic, TypeVar

from pydantic import BaseModel, Field

TipoDoItem = TypeVar("TipoDoItem")


# envelope de toda listagem paginada; Generic permite Pagina[ResumoDoSanto], Pagina[ResumoDoLivro]...
class Pagina(BaseModel, Generic[TipoDoItem]):
    itens: list[TipoDoItem]
    pagina: int = Field(description="Página atual (começa em 1).")
    limite: int = Field(description="Itens por página (no máximo 20).")
    total_registros_filtros: int = Field(description="Total de registros que atendem aos filtros.")
    total_paginas: int = Field(description="Total de páginas.")


# versão curta do santo, usada dentro de outros objetos (oração, novena, livro)
class ReferenciaDoSanto(BaseModel):
    id: int
    nome: str


# formato padrão dos erros: {"erro": {"codigo", "mensagem", "detalhes"}}
class DetalheDoErro(BaseModel):
    campo: str | None = None
    onde: str | None = Field(default=None, description="Onde aconteceu o erro (query, path...).")
    mensagem: str


class CorpoDoErro(BaseModel):
    codigo: str
    mensagem: str
    detalhes: list[DetalheDoErro] = []


class RespostaDeErro(BaseModel):
    erro: CorpoDoErro


class RespostaDeSaude(BaseModel):
    status: str
    banco: str

"""Schemas compartilhados: paginação, referências e erros."""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    itens: list[T]
    pagina: int = Field(description="Página atual (começa em 1).")
    limite: int = Field(description="Itens por página (máximo 20).")
    total: int = Field(description="Total de registros que atendem aos filtros.")
    total_paginas: int = Field(description="Total de páginas (0 quando não há registros).")


class SantoRef(BaseModel):
    id: int
    nome: str


class ErroDetalhe(BaseModel):
    campo: str | None = None
    local: str | None = Field(default=None, description="query, path, etc.")
    mensagem: str


class ErroCorpo(BaseModel):
    codigo: str
    mensagem: str
    detalhes: list[ErroDetalhe] = []


class ErroResposta(BaseModel):
    erro: ErroCorpo


class SaudeResposta(BaseModel):
    status: str
    banco: str

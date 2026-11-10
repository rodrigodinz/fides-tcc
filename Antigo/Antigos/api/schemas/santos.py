from pydantic import BaseModel, ConfigDict


class SantoResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    foto_url: str | None = None  # caminho relativo (ex.: /static/santos/x.jpg); pode não existir em disco


class OracaoDoSanto(BaseModel):
    id: int
    titulo: str
    basica: bool


class NovenaDoSanto(BaseModel):
    id: int
    titulo: str
    descricao: str | None = None


class LivroDoSanto(BaseModel):
    id: int
    titulo: str
    autor: str


class SantoDetalhe(SantoResumo):
    biografia: str | None = None
    oracoes: list[OracaoDoSanto]
    novenas: list[NovenaDoSanto]
    livros: list[LivroDoSanto]

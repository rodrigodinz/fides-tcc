from pydantic import BaseModel, ConfigDict, Field


class ResumoDoSanto(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # permite montar direto do objeto do SQLAlchemy
    id: int
    nome: str
    foto_url: str | None = Field(default=None, description="Caminho relativo da imagem (ex.: /static/santos/x.jpg).")  # caminho relativo (ex.: /static/santos/x.jpg); pode não existir em disco, então a gente vai ter que colocar as imagens que vão estar no git ou no pen drive no computador, no dia da apresentacao


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


# herda id, nome e foto do resumo e acrescenta biografia e os vínculos
class DetalhesDoSanto(ResumoDoSanto):
    biografia: str | None = None
    oracoes: list[OracaoDoSanto]
    novenas: list[NovenaDoSanto]
    livros: list[LivroDoSanto]

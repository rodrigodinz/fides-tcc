from pydantic import BaseModel, Field

from .comum import ReferenciaDoSanto


class ConteudoDoMomento(BaseModel):
    id: int
    codigo: str = Field(description="Ex.: ao_acordar.")  # tipo, ao acordar
    nome: str = Field(description="Ex.: Ao acordar.")    # tipo, "Ao acordar"


# a oração vem com o texto inteiro e os momentos do dia em que aparece
class ConteudoDaOracao(BaseModel):
    id: int
    titulo: str
    texto: str
    basica: bool
    santo: ReferenciaDoSanto | None = Field(default=None, description="Null nas orações gerais (ex.: Pai Nosso).")  #Nulo nas oracoes gerais, tipo pai nosso
    momentos: list[ConteudoDoMomento]

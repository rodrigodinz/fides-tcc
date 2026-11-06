from datetime import date

from pydantic import BaseModel, Field


class IntervaloLiturgia(BaseModel):
    hoje: date
    inicio: date = Field(description="Primeira dia da liturgia (Hoje - 7 dias).")
    fim: date = Field(description="Última dia da liturgia (hoje + 7 dias).")


class BlocoRef(BaseModel):
    codigo: str  # laudes, horas_medias, vesperas
    nome: str


class HoraItem(BaseModel):
    bloco: BlocoRef
    texto: str


class LiturgiaHorasResposta(BaseModel):
    data: date
    intervalo: IntervaloLiturgia
    horas: list[HoraItem]
    aviso: str


class LeiturasDoDia(BaseModel):
    santo_celebrado: str | None = None
    primeira_leitura: str | None = None
    salmo: str | None = None
    evangelho: str | None = None
    segunda_leitura: str | None = None
    possui_segunda_leitura: bool


class LiturgiaDiaResposta(LeiturasDoDia):
    data: date
    intervalo: IntervaloLiturgia
    aviso: str

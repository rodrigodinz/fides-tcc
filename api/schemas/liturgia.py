from datetime import date

from pydantic import BaseModel, Field


class IntervaloLiturgia(BaseModel):
    hoje: date
    inicio: date = Field(description="Primeira data consultável (hoje - 7 dias).")
    fim: date = Field(description="Última data consultável (hoje + 7 dias).")


class BlocoRef(BaseModel):
    codigo: str  # laudes | horas_medias | vesperas
    nome: str


class HoraItem(BaseModel):
    bloco: BlocoRef
    texto: str


class LiturgiaHorasResposta(BaseModel):
    data: date
    intervalo: IntervaloLiturgia
    horas: list[HoraItem]
    avisos_integridade: list[str] = Field(
        default=[], description="Preenchido só se o banco tiver dados inconsistentes (ex.: bloco repetido).")
    aviso: str


class LiturgiaDiaResposta(BaseModel):
    data: date
    intervalo: IntervaloLiturgia
    santo_celebrado: str | None = None
    primeira_leitura: str | None = None
    salmo: str | None = None
    evangelho: str | None = None
    segunda_leitura: str | None = None  # só quando cadastrada (domingos/festas)
    possui_segunda_leitura: bool
    aviso: str

from datetime import date

from pydantic import BaseModel, Field


# janela disponível (hoje ± 7 dias); o front usa para limitar o calendário
class PeriodoDaLiturgia(BaseModel):
    hoje: date
    inicio: date = Field(description="Primeiro dia com liturgia disponível (hoje - 7 dias).")
    fim: date = Field(description="Último dia com liturgia disponível (hoje + 7 dias).")


class ReferenciaDoBloco(BaseModel):
    codigo: str  # laudes, horas_medias, vesperas
    nome: str


class HoraDaLiturgia(BaseModel):
    bloco: ReferenciaDoBloco
    texto: str


class RespostaLiturgiaDasHoras(BaseModel):
    data: date
    periodo: PeriodoDaLiturgia
    horas: list[HoraDaLiturgia]
    aviso: str


# só as leituras; é reaproveitado na resposta da agenda
class LeiturasDoDia(BaseModel):
    santo_celebrado: str | None = None
    primeira_leitura: str | None = None
    salmo: str | None = None
    evangelho: str | None = None
    segunda_leitura: str | None = None
    tem_segunda_leitura_no_dia: bool


# herda os campos de LeiturasDoDia e acrescenta data, período e aviso
class RespostaLiturgiaDoDia(LeiturasDoDia):
    data: date
    periodo: PeriodoDaLiturgia
    aviso: str

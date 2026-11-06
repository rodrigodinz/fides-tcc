from datetime import date, timedelta

from sqlalchemy.orm import Session

from database.models import Periodo_Disponivel_De_Liturgias, BlocoLiturgia, LiturgiaDia, LiturgiaHora

from ..errors import Erro_Da_Api
from ..schemas.liturgia import (HoraDaLiturgia, LeiturasDoDia, PeriodoDaLiturgia, ReferenciaDoBloco,
                                RespostaLiturgiaDasHoras, RespostaLiturgiaDoDia)

# Remover esse texto na Fase 2 do projeto
Aviso_Demonstracao = ("Conteúdo de demonstração: estes textos não correspondem à liturgia oficial. "
                      "Serão substituídos por fonte oficial na Fase 2 do Fides.")

Ordem_Dos_Blocos = {bloco: posicao for posicao, bloco in enumerate(BlocoLiturgia)}


def periodo_da_liturgia() -> PeriodoDaLiturgia:
    hoje = date.today()
    dias_disponiveis = timedelta(days=Periodo_Disponivel_De_Liturgias)
    return PeriodoDaLiturgia(hoje=hoje, inicio=hoje - dias_disponiveis, fim=hoje + dias_disponiveis)


def _erro_liturgia_nao_cadastrada(data: date) -> Erro_Da_Api:
    return Erro_Da_Api(404, "LITURGIA_NAO_CADASTRADA",
                       f"Não há liturgia cadastrada para {data.isoformat()}.")


def montar_leituras_do_dia(liturgia_do_dia: LiturgiaDia) -> LeiturasDoDia:
    tem_segunda_leitura = liturgia_do_dia.tem_segunda_leitura_no_dia()
    return LeiturasDoDia(
        santo_celebrado=liturgia_do_dia.santo_celebrado, primeira_leitura=liturgia_do_dia.primeira_leitura,
        salmo=liturgia_do_dia.salmo, evangelho=liturgia_do_dia.evangelho,
        segunda_leitura=liturgia_do_dia.segunda_leitura if tem_segunda_leitura else None,
        tem_segunda_leitura_no_dia=tem_segunda_leitura)


def ordenar_horas_da_liturgia(registros) -> list[HoraDaLiturgia]:
    return [HoraDaLiturgia(bloco=ReferenciaDoBloco(codigo=registro.bloco.name.lower(), nome=registro.bloco.value),
                           texto=registro.texto)
            for registro in sorted(registros, key=lambda registro: Ordem_Dos_Blocos[registro.bloco])]


def consultar_liturgia_das_horas(session: Session, data: date | None,
                                 bloco: BlocoLiturgia | None) -> RespostaLiturgiaDasHoras:
    data = data or date.today()
    if bloco is None:
        registros = LiturgiaHora.buscar_por_data(session, data)
    else:
        registro_do_bloco = LiturgiaHora.buscar_por_bloco(session, data, bloco)
        registros = [registro_do_bloco] if registro_do_bloco is not None else []
    if not registros:
        raise _erro_liturgia_nao_cadastrada(data)
    return RespostaLiturgiaDasHoras(data=data, periodo=periodo_da_liturgia(), aviso=Aviso_Demonstracao,
                                    horas=ordenar_horas_da_liturgia(registros))


def consultar_liturgia_do_dia(session: Session, data: date | None) -> RespostaLiturgiaDoDia:
    data = data or date.today()
    liturgia_do_dia = LiturgiaDia.buscar_por_data(session, data)
    if liturgia_do_dia is None:
        raise _erro_liturgia_nao_cadastrada(data)
    return RespostaLiturgiaDoDia(data=data, periodo=periodo_da_liturgia(), aviso=Aviso_Demonstracao,
                                 **montar_leituras_do_dia(liturgia_do_dia).model_dump())

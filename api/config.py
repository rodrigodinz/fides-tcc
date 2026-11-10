"""Variáveis de ambiente da API (as do banco, como FIDES_DATABASE_URL e
FIDES_SECRET_KEY, continuam sendo lidas por ``database/``):

    FIDES_CORS_ORIGINS  origens extras permitidas, separadas por vírgula; só é preciso se o
                        front-end for aberto em outro endereço (padrão: http://localhost:8000,http://127.0.0.1:8000)
    FIDES_STATIC_DIR    diretório servido em /static (padrão: <raiz>/static)
    FIDES_FRONTEND_DIR  diretório das páginas do site, servido em / (padrão: <raiz>/frontend)
    FIDES_TIMEZONE      fuso usado para "hoje" (padrão: America/Sao_Paulo)
"""
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("fides.api")

Base_Do_Diretorio = Path(__file__).resolve().parent.parent
Origens_Padrao = "http://localhost:8000,http://127.0.0.1:8000"
Fuso_Horario_Padrao = "America/Sao_Paulo"


@dataclass(frozen=True)
class Configuracoes:
    origens_permitidas: tuple
    diretorio_estatico: Path
    diretorio_do_frontend: Path
    fuso_horario: str


def ler_configuracoes() -> Configuracoes:
    origens = os.getenv("FIDES_CORS_ORIGINS", Origens_Padrao)
    return Configuracoes(
        origens_permitidas=tuple(origem.strip().rstrip("/") for origem in origens.split(",") if origem.strip()),
        diretorio_estatico=Path(os.getenv("FIDES_STATIC_DIR") or Base_Do_Diretorio / "static"),
        diretorio_do_frontend=Path(os.getenv("FIDES_FRONTEND_DIR") or Base_Do_Diretorio / "frontend"),
        fuso_horario=os.getenv("FIDES_TIMEZONE") or Fuso_Horario_Padrao,
    )


def aplicar_fuso_horario(nome_do_fuso: str) -> bool:
    if not hasattr(time, "tzset"):
        logger.info("time.tzset indisponível; usando o fuso do sistema operacional.")
        return False
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(nome_do_fuso)
    except Exception:
        logger.warning("FIDES_TIMEZONE inválido ('%s'); mantendo o fuso atual.", nome_do_fuso)
        return False
    os.environ["TZ"] = nome_do_fuso
    time.tzset()
    return True

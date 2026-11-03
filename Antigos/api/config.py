"""Configuração da API, lida das variáveis de ambiente.

Variáveis próprias da API (as do banco, como FIDES_DATABASE_URL e
FIDES_SECRET_KEY, continuam sendo lidas por ``database/``):

    FIDES_CORS_ORIGINS  origens permitidas, separadas por vírgula
                        (padrão: http://localhost:5173,http://localhost:3000)
    FIDES_STATIC_DIR    diretório servido em /static (padrão: <raiz>/static)
    FIDES_TIMEZONE      fuso usado para "hoje" (padrão: America/Sao_Paulo)
"""
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("fides.api")

BASE_DIR = Path(__file__).resolve().parent.parent
ORIGENS_PADRAO = "http://localhost:5173,http://localhost:3000"
FUSO_PADRAO = "America/Sao_Paulo"


@dataclass(frozen=True)
class Settings:
    cors_origins: tuple
    static_dir: Path
    timezone: str


def get_settings() -> Settings:
    origens = os.getenv("FIDES_CORS_ORIGINS", ORIGENS_PADRAO)
    return Settings(
        cors_origins=tuple(o.strip().rstrip("/") for o in origens.split(",") if o.strip()),
        static_dir=Path(os.getenv("FIDES_STATIC_DIR") or BASE_DIR / "static"),
        timezone=os.getenv("FIDES_TIMEZONE") or FUSO_PADRAO,
    )


def aplicar_fuso_horario(nome: str) -> bool:
    """Ajusta o fuso do processo para que ``date.today()`` seja a data do Brasil.

    O modelo (``Liturgia._dentro_intervalo``) usa ``date.today()``. Em vez de
    criar uma segunda regra de intervalo na API, o fuso do próprio processo é
    ajustado, de modo que o modelo e a API enxerguem a mesma data. Só funciona
    onde existe ``time.tzset`` (Linux/macOS); no Windows vale o fuso do sistema.
    Retorna True se o fuso foi aplicado.
    """
    if not hasattr(time, "tzset"):
        logger.info("time.tzset indisponível; usando o fuso do sistema operacional.")
        return False
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(nome)  # valida o nome (o glibc ignoraria silenciosamente um nome inválido)
    except Exception:
        logger.warning("FIDES_TIMEZONE inválido ('%s'); mantendo o fuso atual.", nome)
        return False
    os.environ["TZ"] = nome
    time.tzset()
    return True

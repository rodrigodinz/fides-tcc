"""Normalização de termos de busca.

O banco guarda ``Santo.nome_busca`` (minúsculas, sem acento). Como o helper do
modelo (``_normalizar``) é privado, a API tem a sua própria implementação; um
teste garante que as duas coincidem para todos os santos cadastrados.
"""
import unicodedata


def normalizar_busca(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def escapar_like(termo: str) -> str:
    """Escapa %, _ e a própria barra para uso com ``like(..., escape="\\\\")``."""
    return termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

import unicodedata


def normalizar_texto_da_busca(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


def escapar_caracteres_do_like(texto_buscado: str) -> str:
    return texto_buscado.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

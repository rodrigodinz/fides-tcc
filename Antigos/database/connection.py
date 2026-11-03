# Conexão com o banco de dados do FIDES (SQLite + SQLAlchemy).

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("FIDES_DATABASE_URL", f"sqlite:///{BASE_DIR / 'database.db'}")

Base = declarative_base()


def criar_engine(url: str = DATABASE_URL, echo: bool = False):
    engine = create_engine(url, echo=echo, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def _ativar_chaves_estrangeiras(conexao, _):
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = criar_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def criar_tabelas(alvo=None):
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=alvo or engine)


def apagar_tabelas(alvo=None):
    from . import models  # noqa: F401

    Base.metadata.drop_all(bind=alvo or engine)

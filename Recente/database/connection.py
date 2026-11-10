import os
from pathlib import Path

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

Base_Do_Diretorio = Path(__file__).resolve().parent.parent
Url_Do_Banco = os.getenv("FIDES_DATABASE_URL", f"sqlite:///{Base_Do_Diretorio / 'database.db'}")

Base = declarative_base()


def criar_engine(url: str = Url_Do_Banco, echo: bool = False):
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
    from . import models

    Base.metadata.create_all(bind=alvo or engine)


def apagar_tabelas(alvo=None):
    alvo = alvo or engine
    tabelas_que_existem = MetaData()
    tabelas_que_existem.reflect(bind=alvo)
    with alvo.begin() as conexao:
        if conexao.dialect.name == "sqlite":
            conexao.exec_driver_sql("PRAGMA foreign_keys=OFF")
        tabelas_que_existem.drop_all(bind=conexao)
        if conexao.dialect.name == "sqlite":
            conexao.exec_driver_sql("PRAGMA foreign_keys=ON")

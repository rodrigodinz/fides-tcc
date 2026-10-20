"""Helpers de teste da API: bancos SQLite TEMPORÁRIOS em arquivo, isolados do database.db."""
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from api.main import create_app
from database.connection import criar_engine, criar_tabelas, get_session
from database.seeds import popular_banco


def montar_banco(tmp_path_factory, nome, referencia=None, popular=True):
    caminho = tmp_path_factory.mktemp(nome) / "fides_teste.db"
    engine = criar_engine(f"sqlite:///{caminho}")
    fabrica = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    if popular:
        criar_tabelas(engine)
        with fabrica() as sessao:
            popular_banco(sessao, data_referencia=referencia)
    return fabrica


def montar_cliente(fabrica) -> TestClient:
    app = create_app()

    def _sessao_de_teste():
        sessao = fabrica()
        try:
            yield sessao
        finally:
            sessao.close()

    app.dependency_overrides[get_session] = _sessao_de_teste
    # raise_server_exceptions=False: queremos ver o 500 que o cliente real veria.
    return TestClient(app, raise_server_exceptions=False)

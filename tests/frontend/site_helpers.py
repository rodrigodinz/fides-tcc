from sqlalchemy.orm import sessionmaker

from api.main import criar_aplicacao
from database.connection import criar_engine, criar_tabelas, get_session
from database.seeds import popular_banco


def montar_aplicacao_de_teste(tmp_path_factory):
    """Aplicação completa (API + site) usando um banco SQLite temporário com os seeds."""
    caminho = tmp_path_factory.mktemp("site") / "fides_site.db"
    engine = criar_engine(f"sqlite:///{caminho}")
    fabrica = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    criar_tabelas(engine)
    with fabrica() as sessao:
        popular_banco(sessao)

    app = criar_aplicacao()

    def _sessao_de_teste():
        sessao = fabrica()
        try:
            yield sessao
        finally:
            sessao.close()

    app.dependency_overrides[get_session] = _sessao_de_teste
    return app


def pagina_de(itens):
    """Envelope de paginação igual ao da API, para respostas inventadas."""
    return {"itens": itens, "pagina": 1, "limite": 20, "total_registros_filtros": len(itens), "total_paginas": 1 if itens else 0}


def erro_da_api(codigo):
    return {"erro": {"codigo": codigo, "mensagem": "x", "detalhes": []}}

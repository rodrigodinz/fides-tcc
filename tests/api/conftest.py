"""Fixtures da API: bancos SQLite TEMPORÁRIOS em arquivo, isolados do database.db.

Usa o engine/seeds reais da aplicação (``criar_engine``, ``criar_tabelas``,
``popular_banco``) sobre um arquivo em diretório temporário e substitui a
dependência ``get_session``. Nada aqui lê ou escreve o banco de desenvolvimento.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy.orm import sessionmaker

from fides_helpers import montar_banco, montar_cliente
from database.connection import criar_engine
from database.models import BlocoLiturgia, LiturgiaHora


@pytest.fixture(scope="session")
def fabrica(tmp_path_factory):
    return montar_banco(tmp_path_factory, "principal")


@pytest.fixture(scope="session")
def cliente(fabrica):
    return montar_cliente(fabrica)


@pytest.fixture()
def sessao(fabrica):
    """Sessão direta ao banco temporário, usada como 'oráculo' independente nos testes."""
    with fabrica() as s:
        yield s


@pytest.fixture(scope="session")
def cliente_liturgia_defasada(tmp_path_factory):
    """Liturgia semeada em torno de hoje-3: cobre hoje-10..hoje+4.
    Logo, hoje+5..hoje+7 estão DENTRO da janela, mas SEM registro."""
    referencia = date.today() - timedelta(days=3)
    return montar_cliente(montar_banco(tmp_path_factory, "defasado", referencia))


@pytest.fixture(scope="session")
def cliente_hora_duplicada(tmp_path_factory):
    """Banco com um bloco de LiturgiaHora repetido na mesma data (o banco permite)."""
    fabrica = montar_banco(tmp_path_factory, "duplicado")
    hoje = date.today()
    with fabrica() as s:
        s.add(LiturgiaHora(data=hoje, bloco=BlocoLiturgia.LAUDES, texto="[Demonstração] LAUDES duplicada"))
        s.commit()
    return montar_cliente(fabrica)


@pytest.fixture(scope="session")
def cliente_sem_tabelas(tmp_path_factory):
    """Banco acessível, porém sem tabelas: falha de consulta (bug), não indisponibilidade."""
    return montar_cliente(montar_banco(tmp_path_factory, "vazio", popular=False))


@pytest.fixture(scope="session")
def cliente_banco_inacessivel(tmp_path_factory):
    """Engine apontando para um diretório inexistente: o SQLite não consegue abrir o arquivo."""
    inexistente = tmp_path_factory.mktemp("base") / "nao_existe" / "x.db"
    engine = criar_engine(f"sqlite:///{inexistente}")
    return montar_cliente(sessionmaker(bind=engine, autoflush=False, expire_on_commit=False))

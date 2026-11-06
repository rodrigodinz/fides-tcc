"""Fixtures da API: bancos SQLite TEMPORÁRIOS em arquivo, isolados do database.db.

Usa o engine/seeds reais da aplicação (``criar_engine``, ``criar_tabelas``,
``popular_banco``) sobre um arquivo em diretório temporário e substitui a
dependência ``get_session``. Nada aqui lê ou escreve o banco de desenvolvimento.
"""
from datetime import date, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from fides_helpers import montar_banco, montar_cliente
from database.connection import criar_engine
from database.models import Administrador, Agenda, Novena, Oracao, TipoAgenda


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
    """Seeds com data de referência hoje-3: a liturgia cobre hoje-10..hoje+4.
    Logo, hoje+5..hoje+7 estão DENTRO da janela, mas SEM registro. As agendas
    das novenas também ficam deslocadas 3 dias para trás."""
    referencia = date.today() - timedelta(days=3)
    return montar_cliente(montar_banco(tmp_path_factory, "defasado", referencia))


def _token_admin(sessao):
    """Token do administrador semeado, só para PREPARAR cenários de teste com os
    métodos de escrita do modelo (a API não tem rotas de escrita)."""
    return sessao.scalar(select(Administrador)).emitir_token()


@pytest.fixture(scope="session")
def cliente_cancelado(tmp_path_factory):
    """Banco em que o administrador cancelou a agenda da novena de Santa Teresa
    d'Ávila e a agenda de liturgia (UC07, UC09): esses conteúdos deixam de aparecer."""
    fabrica = montar_banco(tmp_path_factory, "cancelado")
    with fabrica() as s:
        token = _token_admin(s)
        teresa = s.scalar(select(Novena).where(Novena.titulo == "Novena a Santa Teresa d'Ávila"))
        Agenda.buscar_ativa(s, teresa.id).cancelar(token)
        for agenda in Agenda.listar_ativas(s, TipoAgenda.LITURGIA):
            agenda.cancelar(token)
        s.commit()
    return montar_cliente(fabrica)


@pytest.fixture(scope="session")
def cliente_novena_sem_santo(tmp_path_factory):
    """Banco com uma novena SEM santo (permitido desde a remodelagem, UML 0..1),
    agendada para começar hoje."""
    fabrica = montar_banco(tmp_path_factory, "sem_santo")
    with fabrica() as s:
        token = _token_admin(s)
        pai_nosso = s.scalar(select(Oracao).where(Oracao.titulo == "Pai Nosso", Oracao.santo_id.is_(None)))
        novena = Novena.cadastrar(s, {
            "titulo": "Novena de teste sem santo", "descricao": "Cenário de teste.",
            "dias": [{"texto_reflexao": f"Reflexão {n}", "oracoes_base_ids": [pai_nosso.id]}
                     for n in range(1, 10)]}, token)
        Agenda.agendar_novena(s, novena.id, date.today(), token)
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

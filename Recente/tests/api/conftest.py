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
    with fabrica() as s:
        yield s


@pytest.fixture(scope="session")
def cliente_liturgia_defasada(tmp_path_factory):
    referencia = date.today() - timedelta(days=3)
    return montar_cliente(montar_banco(tmp_path_factory, "defasado", referencia))


def _token_admin(sessao):
    return sessao.scalar(select(Administrador)).emitir_token()


@pytest.fixture(scope="session")
def cliente_cancelado(tmp_path_factory):
    fabrica = montar_banco(tmp_path_factory, "cancelado")
    with fabrica() as s:
        token = _token_admin(s)
        teresa = s.scalar(select(Novena).where(Novena.titulo == "Novena a Santa Teresa d'Ávila"))
        Agenda.buscar_agenda_ativa_da_novena(s, teresa.id).cancelar(token)
        for agenda in Agenda.listar_agendas_ativas(s, TipoAgenda.LITURGIA):
            agenda.cancelar(token)
        s.commit()
    return montar_cliente(fabrica)


@pytest.fixture(scope="session")
def cliente_novena_sem_santo(tmp_path_factory):
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
    return montar_cliente(montar_banco(tmp_path_factory, "vazio", popular=False))


@pytest.fixture(scope="session")
def cliente_banco_inacessivel(tmp_path_factory):
    inexistente = tmp_path_factory.mktemp("base") / "nao_existe" / "x.db"
    engine = criar_engine(f"sqlite:///{inexistente}")
    return montar_cliente(sessionmaker(bind=engine, autoflush=False, expire_on_commit=False))

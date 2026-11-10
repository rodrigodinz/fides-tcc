import pytest
from sqlalchemy import func, select

from database.models import Livro

URL = "/api/v1/livros"


def test_listagem_e_campos(cliente, sessao):
    c = cliente.get(URL).json()
    assert c["total"] == sessao.scalar(select(func.count()).select_from(Livro))
    assert all(set(i) == {"id", "titulo", "autor", "santo"} for i in c["itens"])
    titulos = [i["titulo"] for i in c["itens"]]
    assert titulos == sorted(titulos)


def test_paginacao_sem_repeticao(cliente, sessao):
    total = sessao.scalar(select(func.count()).select_from(Livro))
    ids = []
    for p in range(1, total + 1):
        ids += [i["id"] for i in cliente.get(URL, params={"pagina": p, "limite": 1}).json()["itens"]]
    assert len(ids) == len(set(ids)) == total
    assert cliente.get(URL, params={"pagina": total + 1, "limite": 1}).json()["itens"] == []


def test_santo_nulo_e_preenchido_conforme_o_banco(cliente, sessao):
    itens = cliente.get(URL).json()["itens"]
    for i in itens:
        banco = sessao.get(Livro, i["id"])
        assert (i["santo"] is None) == (banco.santo_id is None)
        if banco.santo_id:
            assert i["santo"] == {"id": banco.santo.id, "nome": banco.santo.nome}
    assert any(i["santo"] is None for i in itens) and any(i["santo"] for i in itens)


def test_filtro_por_santo(cliente, sessao):
    santo_id = sessao.scalar(select(Livro.santo_id).where(Livro.santo_id.is_not(None)))
    esperado = set(sessao.scalars(select(Livro.id).where(Livro.santo_id == santo_id)))
    c = cliente.get(URL, params={"santo_id": santo_id}).json()
    assert {i["id"] for i in c["itens"]} == esperado and c["total"] == len(esperado)
    assert cliente.get(URL, params={"santo_id": 99999}).json()["itens"] == []


def test_detalhe_com_resumo_e_contexto(cliente, sessao):
    for livro in sessao.scalars(select(Livro)):
        d = cliente.get(f"{URL}/{livro.id}").json()
        assert set(d) == {"id", "titulo", "autor", "santo", "resumo", "contexto_historico"}
        assert d["resumo"] == livro.resumo and d["contexto_historico"] == livro.contexto_historico
        assert d["autor"] == livro.autor


def test_livro_sem_santo_no_detalhe(cliente, sessao):
    livro = sessao.scalar(select(Livro).where(Livro.santo_id.is_(None)))
    r = cliente.get(f"{URL}/{livro.id}")
    assert r.status_code == 200 and r.json()["santo"] is None


def test_livro_inexistente_404(cliente):
    r = cliente.get(f"{URL}/99999")
    assert r.status_code == 404 and r.json()["erro"]["codigo"] == "RECURSO_NAO_ENCONTRADO"


@pytest.mark.parametrize("params", [{"limite": 21}, {"pagina": 0}, {"santo_id": 0}])
def test_parametros_invalidos_422(cliente, params):
    assert cliente.get(URL, params=params).status_code == 422


def test_id_invalido_422(cliente):
    assert cliente.get(f"{URL}/abc").status_code == 422


# ------------------- Recomendação de leitura (UC13, US12) -------------------
REC = "/api/v1/livros/recomendados"


def _santo_id(sessao, trecho):
    from database.models import Santo
    return sessao.scalar(select(Santo.id).where(Santo.nome_busca.like(f"%{trecho}%")))


def test_recomenda_os_livros_do_santo_acessado(cliente, sessao):
    agostinho = _santo_id(sessao, "agostinho")
    c = cliente.get(REC, params={"santo_id": agostinho}).json()
    esperado = set(sessao.scalars(select(Livro.titulo).where(Livro.santo_id == agostinho)))
    assert {i["titulo"] for i in c["itens"]} == esperado and "Confissões" in esperado
    assert all(i["santo"]["id"] == agostinho for i in c["itens"])


def test_recomendacao_de_varios_santos_acessados(cliente, sessao):
    ids = [_santo_id(sessao, "agostinho"), _santo_id(sessao, "josemaria"), _santo_id(sessao, "agostinho")]
    c = cliente.get(REC, params={"santo_id": ids}).json()
    esperado = set(sessao.scalars(select(Livro.id).where(Livro.santo_id.in_(set(ids)))))
    assert {i["id"] for i in c["itens"]} == esperado and c["total"] == len(esperado) >= 2
    titulos = [i["titulo"] for i in c["itens"]]
    assert titulos == sorted(titulos)


def test_livros_sem_santo_nunca_sao_recomendados(cliente, sessao):
    from database.models import Santo
    todos = list(sessao.scalars(select(Santo.id)))
    ids = {i["id"] for i in cliente.get(REC, params={"santo_id": todos}).json()["itens"]}
    sem_santo = set(sessao.scalars(select(Livro.id).where(Livro.santo_id.is_(None))))
    assert sem_santo and not ids & sem_santo


def test_recomendacao_nao_usa_a_marcacao_livro_recomendado(cliente, sessao):
    # A decisão é recomendar pelos santos acessados; a coluna do banco não é exposta.
    for url in (URL, REC + "?santo_id=1", f"{URL}/1"):
        assert "recomendado" not in cliente.get(url).text


def test_recomendacao_santo_inexistente_vazio(cliente):
    r = cliente.get(REC, params={"santo_id": 99999})
    assert r.status_code == 200 and r.json()["itens"] == []


@pytest.mark.parametrize("params", [{}, {"santo_id": 0}, {"santo_id": "x"},
                                    {"santo_id": list(range(1, 22))}, {"santo_id": 1, "limite": 21}])
def test_recomendacao_parametros_invalidos_422(cliente, params):
    r = cliente.get(REC, params=params)
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"

"""Cenários das páginas com respostas da API inventadas (lista vazia, falha de rede, 404...)."""
import json

from site_helpers import erro_da_api, pagina_de

Periodo_De_Teste = {"hoje": "2026-11-05", "inicio": "2026-10-29", "fim": "2026-11-12"}
Dias_Sem_Agenda = [{"id": numero, "numero_do_dia": numero, "data": None} for numero in range(1, 10)]


def test_santos_lista_vazia_mostra_estado_vazio_e_nao_erro(site):
    site.responder_api("/santos?", pagina_de([]))
    pagina = site.abrir("/santos.html?nome=francisco")
    assert pagina.get_by_text("Nenhum santo encontrado para “francisco”").is_visible()
    assert pagina.locator('[role="alert"]').count() == 0


def test_santos_falha_de_rede_mostra_mensagem_e_tenta_de_novo(site):
    estado = {"falhar": True}

    def _responder(rota):
        if estado["falhar"]:
            rota.abort()
        else:
            rota.fulfill(content_type="application/json", body=json.dumps(pagina_de([{"id": 1, "nome": "São Tomás de Aquino", "foto_url": None}])))
    site.responder_api("/santos?", funcao=_responder)
    pagina = site.abrir("/santos.html")
    assert pagina.get_by_text("Não foi possível carregar os santos no momento.").is_visible()
    estado["falhar"] = False
    pagina.get_by_role("button", name="Tentar novamente").click()
    link = pagina.get_by_role("link", name="São Tomás de Aquino")
    link.wait_for()
    assert link.get_attribute("href") == "/santo.html?id=1"
    assert pagina.get_by_text("Retrato não disponível").is_visible()


def test_santo_registra_o_acesso_e_nao_busca_oracoes_inexistentes(site):
    site.responder_api("/santos/5", {"id": 5, "nome": "Santa Teresa d'Ávila", "foto_url": None, "biografia": "Carmelita.",
                                     "oracoes": [], "novenas": [], "livros": [{"id": 1, "titulo": "O Castelo Interior", "autor": "Santa Teresa de Jesus"}]})
    pagina = site.abrir("/santo.html?id=5")
    assert pagina.get_by_role("heading", level=1, name="Santa Teresa d'Ávila").is_visible()
    assert pagina.evaluate("localStorage.getItem('fides:v1:santos-acessados')") == "[5]"
    assert pagina.get_by_role("link", name="O Castelo Interior").get_attribute("href") == "/livro.html?id=1"
    assert not any("/oracoes" in url for url in site.chamadas_a_api)
    assert pagina.title() == "Santa Teresa d'Ávila · Fides"


def test_santo_inexistente_mostra_nao_encontrado(site):
    site.responder_api("/santos/999", erro_da_api("RECURSO_NAO_ENCONTRADO"), status=404)
    pagina = site.abrir("/santo.html?id=999")
    assert pagina.get_by_text("Santo não encontrado").is_visible()


def test_id_invalido_na_url_nem_chama_a_api(site):
    pagina = site.abrir("/livro.html?id=abc")
    assert pagina.get_by_text("Livro não encontrado").is_visible()
    assert site.chamadas_a_api == []


def test_novena_sem_agenda_nao_inventa_data_e_marcacao_fica_so_no_aparelho(site):
    site.responder_api("/novenas/3/dias/1", {"novena": {"id": 3, "titulo": "Novena X"}, "numero_do_dia": 1, "total_dias": 9, "data": None,
                                             "dia_atual": None, "texto_reflexao": "Reflexão um.", "oracoes": [], "dia_anterior": None, "proximo_dia": 2})
    site.responder_api("/novenas/3/dias", {"novena": {"id": 3, "titulo": "Novena X"}, "total_dias": 9, "agenda": None, "dias": Dias_Sem_Agenda})
    site.responder_api("/novenas/3", {"id": 3, "titulo": "Novena X", "descricao": None, "santo": None, "total_dias": 9, "agenda": None})
    pagina = site.abrir("/novena.html?id=3")
    assert pagina.get_by_text("Reflexão um.").is_visible()
    assert pagina.get_by_text("Não agendada").count() > 0
    assert pagina.get_by_text("Hoje", exact=True).count() == 0
    pagina.get_by_label("Rezei o dia 1").check()
    assert json.loads(pagina.evaluate("localStorage.getItem('fides:v1:novena:3')"))["marcados"] == [1]
    calendario = pagina.get_by_role("list", name="Os nove dias da novena")
    assert calendario.get_by_role("link", name="Dia 1, marcado como rezado neste dispositivo, aberto").is_visible()
    assert pagina.get_by_text("Não agendada").count() > 0


def test_livros_sem_santos_acessados_nao_chama_recomendados(site):
    site.responder_api("/santos?", pagina_de([]))
    site.responder_api("/livros?", pagina_de([{"id": 6, "titulo": "Teologia do Corpo", "autor": "São João Paulo II", "santo": None}]))
    pagina = site.abrir("/livros.html")
    assert pagina.get_by_role("link", name="Teologia do Corpo").is_visible()
    assert pagina.get_by_text("Ainda sem recomendações").is_visible()
    assert not any("recomendados" in url for url in site.chamadas_a_api)


def test_livros_com_santos_acessados_envia_santo_id_repetido(site):
    site.pagina.add_init_script("localStorage.setItem('fides:v1:santos-acessados', JSON.stringify([2, 5]))")
    site.responder_api("/santos?", pagina_de([]))
    site.responder_api("/livros/recomendados", pagina_de([{"id": 4, "titulo": "História de uma Alma", "autor": "Santa Teresinha", "santo": {"id": 2, "nome": "Santa Teresinha"}}]))
    site.responder_api("/livros?", pagina_de([]))
    pagina = site.abrir("/livros.html")
    assert pagina.get_by_role("link", name="História de uma Alma").is_visible()
    assert any("recomendados?pagina=1&limite=20&santo_id=2&santo_id=5" in url for url in site.chamadas_a_api)


def test_liturgia_fora_do_periodo_mostra_aviso_e_caminho_de_volta(site):
    site.responder_api("/liturgia/dia", erro_da_api("DATA_FORA_DO_INTERVALO"), status=400)
    pagina = site.abrir("/liturgia.html?data=2026-12-30")
    assert pagina.get_by_text("Data fora do período disponível.").is_visible()
    assert pagina.get_by_role("button", name="Ir para hoje").is_visible()


def test_liturgia_mostra_o_aviso_da_api_e_a_segunda_leitura_so_quando_existe(site):
    site.responder_api("/liturgia/dia", {"data": "2026-11-05", "periodo": Periodo_De_Teste, "aviso": "Conteúdo de demonstração.",
                                         "santo_celebrado": None, "primeira_leitura": "L1", "salmo": "S", "evangelho": "E",
                                         "segunda_leitura": None, "tem_segunda_leitura_no_dia": False})
    pagina = site.abrir("/liturgia.html")
    assert pagina.get_by_text("Conteúdo de demonstração.", exact=True).is_visible()
    assert pagina.get_by_role("heading", name="Primeira Leitura").is_visible()
    assert pagina.get_by_role("heading", name="Segunda Leitura").count() == 0


def test_data_invalida_na_url_nem_chama_a_api(site):
    pagina = site.abrir("/agenda.html?data=2026-02-30")
    assert pagina.get_by_text("Data inválida.").is_visible()
    assert site.chamadas_a_api == []


def test_oracoes_sem_imagens_e_filtro_usa_momento_id(site):
    site.responder_api("/momentos", [{"id": 4, "codigo": "antes_de_dormir", "nome": "Antes de dormir"}])
    site.responder_api("/santos?", pagina_de([]))
    site.responder_api("/oracoes?", pagina_de([{"id": 1, "titulo": "Pai Nosso", "texto": "Pai nosso...", "basica": True, "santo": None, "momentos": []}]))
    pagina = site.abrir("/oracoes.html")
    assert pagina.get_by_role("heading", name="Pai Nosso").is_visible()
    assert pagina.locator(".oracao img").count() == 0
    pagina.get_by_role("button", name="Antes de dormir").click()
    pagina.get_by_role("button", name="Antes de dormir", pressed=True).wait_for()
    assert any("/oracoes?" in url and "momento_id=4" in url for url in site.chamadas_a_api)
    assert "momento=4" in pagina.url


def test_texto_da_api_com_html_nao_vira_codigo(site):
    site.responder_api("/livros/1", {"id": 1, "titulo": "<img src=x onerror=alert(1)>", "autor": "<b>autor</b>", "santo": None,
                                     "resumo": "<script>alert(1)</script>", "contexto_historico": None})
    pagina = site.abrir("/livro.html?id=1")
    assert pagina.get_by_role("heading", level=1).inner_text() == "<img src=x onerror=alert(1)>"
    assert pagina.locator("main script, main img[src=x]").count() == 0

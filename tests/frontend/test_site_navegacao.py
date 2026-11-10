"""O site de verdade (API + banco temporário com os seeds): páginas, menus, filtros e marcações."""
import json
from datetime import date, timedelta

import pytest

Paginas_E_Textos = [
    ("/", "Hoje"),
    ("/santos.html", "São Tomás de Aquino"),
    ("/santos.html?nome=teresa", "Santa Teresa d'Ávila"),
    ("/santo.html?id=5", "Nada te perturbe"),
    ("/oracoes.html", "Pai Nosso"),
    ("/oracoes.html?tipo=basicas", "Ave Maria"),
    ("/novenas.html", "Novena a Santa Teresinha"),
    ("/novena.html?id=1", "Os nove dias"),
    ("/novena.html?id=1&dia=3", "Reflexão do dia 3"),
    ("/livros.html", "Catálogo"),
    ("/livro.html?id=1", "Resumo"),
    ("/liturgia.html", "Primeira Leitura"),
    ("/liturgia-horas.html", "Laudes"),
    ("/agenda.html", "Novenas em andamento"),
]


@pytest.mark.parametrize(("endereco", "texto_esperado"), Paginas_E_Textos)
def test_cada_pagina_carrega_o_seu_conteudo(site, endereco, texto_esperado):
    pagina = site.abrir(endereco)
    assert texto_esperado in pagina.locator("main").inner_text()
    assert pagina.locator('[aria-busy="true"]').count() == 0, "a página ficou carregando"
    assert pagina.locator('main [role="alert"]').count() == 0


def test_navbar_e_menu_marcam_a_pagina_atual(site):
    pagina = site.abrir("/santo.html?id=2")
    assert pagina.locator('.link-da-navbar[aria-current="page"]').inner_text() == "Santos"
    assert pagina.locator('#menu-lateral a[aria-current="page"]').text_content() == "Santos"
    pagina = site.abrir("/liturgia-horas.html")
    assert pagina.locator('#menu-lateral a[aria-current="page"]').text_content() == "Liturgia das Horas"


def test_menu_lateral_abre_fecha_com_esc_e_devolve_o_foco(site):
    pagina = site.abrir("/")
    botao_menu = pagina.get_by_role("button", name="Abrir menu")
    botao_menu.click()
    assert pagina.locator("#menu-lateral").get_attribute("aria-hidden") == "false"
    assert botao_menu.get_attribute("aria-expanded") == "true"
    pagina.wait_for_function("document.activeElement?.getAttribute('aria-label') === 'Fechar menu'")
    assert "pagina-sem-rolagem" in pagina.locator("body").get_attribute("class")
    pagina.keyboard.press("Escape")
    assert pagina.locator("#menu-lateral").get_attribute("aria-hidden") == "true"
    pagina.wait_for_function("document.activeElement?.getAttribute('aria-label') === 'Abrir menu'")


def test_foco_fica_preso_dentro_do_menu_aberto(site):
    pagina = site.abrir("/")
    pagina.get_by_role("button", name="Abrir menu").click()
    pagina.wait_for_function("document.activeElement?.getAttribute('aria-label') === 'Fechar menu'")
    for _ in range(12):
        pagina.keyboard.press("Tab")
        assert pagina.evaluate("document.getElementById('menu-lateral').contains(document.activeElement)")


def test_busca_de_santos_grava_na_url_e_filtra(site):
    pagina = site.abrir("/santos.html")
    pagina.get_by_label("Buscar santo").fill("agostinho")
    pagina.wait_for_url("**/santos.html?nome=agostinho")
    pagina.get_by_text("1 santo para “agostinho”").wait_for()
    assert pagina.locator(".card-do-santo").count() == 1
    pagina.get_by_role("button", name="Limpar busca").first.click()
    pagina.wait_for_url("**/santos.html")
    pagina.get_by_text("5 santos").wait_for()


def test_voltar_do_navegador_refaz_a_busca(site):
    pagina = site.abrir("/oracoes.html")
    pagina.get_by_label("Tipo").select_option("basicas")
    pagina.wait_for_url("**tipo=basicas")
    pagina.get_by_role("button", name="Limpar filtros").first.click()
    pagina.wait_for_url("**/oracoes.html")
    pagina.get_by_role("heading", name="Orações básicas").wait_for()


def test_card_de_oracao_longa_abre_e_recolhe(site):
    pagina = site.abrir("/oracoes.html")
    botao = pagina.locator("[data-alternar-oracao]").first
    texto = pagina.locator(f"#{botao.get_attribute('aria-controls')}")
    assert "texto-da-oracao-recolhido" in texto.get_attribute("class")
    botao.click()
    assert botao.get_attribute("aria-expanded") == "true"
    assert "texto-da-oracao-recolhido" not in texto.get_attribute("class")
    assert botao.inner_text() == "Recolher"


def test_novena_abre_no_dia_atual_da_agenda(site):
    pagina = site.abrir("/novena.html?id=1")
    assert pagina.locator(".dia-atual-em-destaque").inner_text().replace("\n", " ").startswith("Dia")
    dia_atual = pagina.locator(".dia-de-hoje .circulo-do-dia").inner_text()
    assert pagina.locator(".dia-selecionado .circulo-do-dia").inner_text() == dia_atual
    assert f"Reflexão do dia {dia_atual}" in pagina.locator("main").inner_text()


def test_marcar_dia_rezado_mostra_aviso_e_marca_o_calendario(site):
    pagina = site.abrir("/novena.html?id=2&dia=4")
    pagina.get_by_label("Rezei o dia 4").check()
    pagina.locator(".aviso-rapido", has_text="Dia 4 marcado como rezado neste dispositivo.").wait_for()
    assert "dia-marcado" in pagina.locator(".dia-do-calendario").nth(3).get_attribute("class")
    assert pagina.get_by_text("Você marcou 1 de 9 dias.").is_visible()
    assert json.loads(pagina.evaluate("localStorage.getItem('fides:v1:novena:2')"))["marcados"] == [4]


def test_pedidos_sao_guardados_e_apagados_com_confirmacao(site):
    pagina = site.abrir("/novena.html?id=2&dia=1")
    pagina.get_by_label("Meus pedidos").fill("Pela minha família")
    assert pagina.get_by_text("18/4000 caracteres").is_visible()
    pagina.get_by_role("button", name="Guardar pedidos").click()
    pagina.locator(".aviso-rapido", has_text="Pedidos guardados neste dispositivo.").wait_for()
    pagina.get_by_role("button", name="Apagar pedidos").click()
    janelaDeConfirmacao = pagina.get_by_role("alertdialog")
    assert janelaDeConfirmacao.get_by_text("Apagar seus pedidos desta novena?").is_visible()
    pagina.keyboard.press("Escape")  # Esc cancela
    assert pagina.get_by_role("alertdialog").count() == 0
    assert pagina.get_by_label("Meus pedidos").input_value() == "Pela minha família"
    pagina.get_by_role("button", name="Apagar pedidos").click()
    pagina.get_by_role("alertdialog").get_by_role("button", name="Apagar pedidos").click()
    pagina.locator(".aviso-rapido", has_text="Pedidos apagados deste dispositivo.").wait_for()
    assert pagina.get_by_label("Meus pedidos").input_value() == ""
    assert pagina.evaluate("localStorage.getItem('fides:v1:novena:2')") is None


def test_seletor_de_data_troca_a_liturgia_e_volta_para_hoje(site):
    pagina = site.abrir("/liturgia.html")
    amanha = (date.today() + timedelta(days=1)).isoformat()
    pagina.get_by_role("button", name="Próximo dia").click()
    pagina.wait_for_url(f"**/liturgia.html?data={amanha}")
    pagina.get_by_role("button", name="Voltar para hoje").wait_for()
    assert pagina.locator("main a.aba").first.get_attribute("href") == f"/liturgia.html?data={amanha}"
    pagina.get_by_role("button", name="Voltar para hoje").click()
    pagina.wait_for_url("**/liturgia.html")


def test_data_fora_do_periodo_volta_para_hoje(site):
    pagina = site.abrir("/agenda.html?data=2000-01-01")
    pagina.get_by_role("button", name="Ir para hoje").click()
    pagina.wait_for_url("**/agenda.html")
    pagina.get_by_role("heading", name="Novenas em andamento").wait_for()


def test_visitar_um_santo_gera_recomendacao_de_livros(site):
    site.abrir("/santo.html?id=2")
    pagina = site.abrir("/livros.html")
    assert pagina.locator("#livros-recomendados .card").count() >= 1
    pagina = site.abrir("/")
    pagina.get_by_role("heading", name="Para continuar a leitura").wait_for()


def test_endereco_inexistente_mostra_a_pagina_404(site):
    resposta = site.pagina.goto(site.endereco_do_site + "/santos/5", wait_until="networkidle")
    assert resposta.status == 404
    assert site.pagina.get_by_role("heading", name="Página não encontrada").is_visible()
    assert site.pagina.get_by_role("link", name="Ir para o início").get_attribute("href") == "/"


def test_rota_inexistente_da_api_continua_respondendo_json(site):
    resposta = site.pagina.request.get(site.endereco_do_site + "/api/v1/nao-existe")
    assert resposta.status == 404
    assert resposta.json()["erro"]["codigo"] == "ROTA_NAO_ENCONTRADA"

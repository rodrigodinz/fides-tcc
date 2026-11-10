"""Identidade visual do site: fontes, ornamentos, cores, layout no celular e capturas de tela.

As capturas de todas as páginas (computador e celular) ficam numa pasta temporária. Para guardá-las
numa pasta sua e conferir a olho, rode com a variável FIDES_PASTA_CAPTURAS, por exemplo:
    FIDES_PASTA_CAPTURAS=capturas python -m pytest tests/frontend/test_site_visual.py
"""
import os
from pathlib import Path

import pytest

Todas_As_Paginas = {
    "inicio": "/", "santos": "/santos.html", "santo": "/santo.html?id=5", "oracoes": "/oracoes.html",
    "novenas": "/novenas.html", "novena": "/novena.html?id=1", "novena_dia_3": "/novena.html?id=1&dia=3",
    "livros": "/livros.html", "livro": "/livro.html?id=1", "liturgia": "/liturgia.html",
    "liturgia_das_horas": "/liturgia-horas.html", "agenda": "/agenda.html", "nao_encontrada": "/pagina-que-nao-existe",
}


def _rolar_ate_o_fim(pagina):
    """Rola a página inteira para as imagens com loading="lazy" carregarem."""
    pagina.evaluate("""async () => {
        for (let y = 0; y < document.body.scrollHeight; y += 400) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 40)); }
        window.scrollTo(0, 0);
    }""")
    pagina.wait_for_load_state("networkidle")


@pytest.mark.parametrize("endereco", Todas_As_Paginas.values(), ids=Todas_As_Paginas.keys())
def test_fontes_do_fides_carregadas(site, endereco):
    pagina = site.abrir(endereco)
    fontes_carregadas = pagina.evaluate("""async () => {
        await document.fonts.ready;
        return [...document.fonts].filter((fonte) => fonte.status === 'loaded').map((fonte) => fonte.family.replace(/["']/g, ''));
    }""")
    assert "Cormorant Garamond" in fontes_carregadas, "títulos sem a fonte Cormorant Garamond"
    assert "Antic" in fontes_carregadas, "textos sem a fonte Antic"


@pytest.mark.parametrize("endereco", Todas_As_Paginas.values(), ids=Todas_As_Paginas.keys())
def test_todas_as_imagens_e_ornamentos_carregam(site, endereco):
    pagina = site.abrir(endereco)
    _rolar_ate_o_fim(pagina)
    imagens_quebradas = pagina.evaluate(
        "[...document.images].filter((imagem) => !imagem.complete || imagem.naturalWidth === 0).map((imagem) => imagem.src)")
    assert imagens_quebradas == []
    assert pagina.locator("img.ornamento").count() >= 1, "a página ficou sem ornamento dourado"


def test_ornamentos_de_fundo_do_css_existem(site):
    pagina = site.abrir("/")
    enderecos_de_fundo = pagina.evaluate("""() => {
        const fundos = [...document.styleSheets].flatMap((folha) => [...folha.cssRules].map((regra) => regra.cssText))
            .join(' ').match(/url\\("?([^")]+\\.svg)"?\\)/g) || [];
        return [...new Set(fundos.map((fundo) => new URL(fundo.replace(/^url\\("?|"?\\)$/g, ''), document.baseURI + 'css/').href))];
    }""")
    assert any("trilho-lateral" in endereco for endereco in enderecos_de_fundo)
    assert any("canto-card" in endereco for endereco in enderecos_de_fundo)
    for endereco in enderecos_de_fundo:
        assert pagina.request.get(endereco).status == 200, endereco


def test_cores_do_tema_aplicadas(site):
    pagina = site.abrir("/")
    cores = pagina.evaluate("""() => {
        const amostra = document.createElement('div');
        amostra.style.background = 'var(--marfim)'; amostra.style.color = 'var(--grafite)';
        document.body.append(amostra);
        const estiloDaAmostra = getComputedStyle(amostra);
        const resultado = { fundoEsperado: estiloDaAmostra.backgroundColor, textoEsperado: estiloDaAmostra.color,
                            fundo: getComputedStyle(document.body).backgroundColor, texto: getComputedStyle(document.body).color,
                            fonteDoTitulo: getComputedStyle(document.querySelector('h1')).fontFamily };
        amostra.remove();
        return resultado;
    }""")
    assert cores["fundo"] == cores["fundoEsperado"] != "rgba(0, 0, 0, 0)"
    assert cores["texto"] == cores["textoEsperado"]
    assert "Cormorant Garamond" in cores["fonteDoTitulo"]


@pytest.mark.parametrize("endereco", Todas_As_Paginas.values(), ids=Todas_As_Paginas.keys())
def test_sem_rolagem_lateral_no_celular(site_no_celular, endereco):
    pagina = site_no_celular.abrir(endereco)
    largura_do_conteudo, largura_da_tela = pagina.evaluate("[document.documentElement.scrollWidth, window.innerWidth]")
    assert largura_do_conteudo <= largura_da_tela


def test_navbar_some_ao_rolar_para_baixo_e_volta_ao_subir(site):
    pagina = site.abrir("/oracoes.html")
    navbar = pagina.locator(".navbar")
    pagina.mouse.wheel(0, 900)
    pagina.wait_for_function("document.querySelector('.navbar').classList.contains('navbar-quando-escondida')")
    pagina.mouse.wheel(0, -300)
    pagina.wait_for_function("!document.querySelector('.navbar').classList.contains('navbar-quando-escondida')")
    assert navbar.is_visible()


def test_cards_em_destaque_tem_os_cantos_dourados(site):
    pagina = site.abrir("/novenas.html")
    assert pagina.locator(".card-de-destaque .cantos-ornamentais-do-card").count() >= 1


@pytest.fixture(scope="module")
def pasta_das_capturas(tmp_path_factory):
    pasta_escolhida = os.getenv("FIDES_PASTA_CAPTURAS")
    pasta = Path(pasta_escolhida) if pasta_escolhida else tmp_path_factory.mktemp("capturas")
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


@pytest.mark.parametrize("nome", Todas_As_Paginas.keys())
def test_capturas_de_tela_de_todas_as_paginas(site, site_no_celular, pasta_das_capturas, nome):
    for aparelho, pagina_de_teste in (("computador", site), ("celular", site_no_celular)):
        pagina = pagina_de_teste.abrir(Todas_As_Paginas[nome])
        _rolar_ate_o_fim(pagina)
        pagina.evaluate("document.fonts.ready")
        arquivo = pasta_das_capturas / f"{aparelho}_{nome}.png"
        pagina.screenshot(path=str(arquivo), full_page=True)
        assert arquivo.stat().st_size > 10_000

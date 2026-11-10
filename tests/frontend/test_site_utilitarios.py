"""Funções JavaScript do site testadas dentro do navegador (sem tela): API, estado e utilitários."""
import pytest


@pytest.fixture()
def js(site):
    """Abre a página 404 (leve) e devolve uma função que roda código JS com import() dos módulos do site."""
    site.abrir("/404.html")

    def rodar(codigo, argumento=None):
        return site.pagina.evaluate(f"async (argumento) => {{ {codigo} }}", argumento)
    return rodar


# ---------------------------------------------------------------- cliente da API
def test_montar_url_usa_pagina_e_limite_e_ignora_vazios(js):
    assert js("""const m = await import('/js/api/cliente.js');
        return m.montarUrlDaRequisicao('/santos', { pagina: 1, limite: 20, nome: '', x: null, y: undefined });""") \
        == "/api/v1/santos?pagina=1&limite=20"


def test_montar_url_repete_o_parametro_para_listas(js):
    assert js("""const m = await import('/js/api/cliente.js');
        return m.montarUrlDaRequisicao('/livros/recomendados', { santo_id: [2, 5] });""") \
        == "/api/v1/livros/recomendados?santo_id=2&santo_id=5"


def test_montar_url_mantem_basica_false(js):
    assert "basica=false" in js("const m = await import('/js/api/cliente.js'); return m.montarUrlDaRequisicao('/oracoes', { basica: false });")


def test_url_da_imagem(js):
    assert js("""const m = await import('/js/api/cliente.js');
        return [m.montarUrlDaImagem('/static/santos/a.jpg'), m.montarUrlDaImagem('static/b.jpg'), m.montarUrlDaImagem(null), m.montarUrlDaImagem('  '),
                m.montarUrlDaImagem('https://x.com/a.jpg')];""") == ["/static/santos/a.jpg", "/static/b.jpg", None, None, "https://x.com/a.jpg"]


def test_buscar_json_devolve_o_corpo_em_caso_de_sucesso(js):
    assert js("const m = await import('/js/api/cliente.js'); return await m.buscarJsonNaApi('/health', {}, { prefixo: '' });") \
        == {"status": "ok", "banco": "ok"}


def test_buscar_json_le_o_envelope_de_erro(js):
    erro = js("""const m = await import('/js/api/cliente.js');
        try { await m.buscarJsonNaApi('/santos/9999'); } catch (e) { return { nome: e.name, codigo: e.codigo, status: e.status }; }""")
    assert erro == {"nome": "ErroDaApi", "codigo": "RECURSO_NAO_ENCONTRADO", "status": 404}


def test_falha_de_rede_vira_FALHA_DE_REDE(site, js):
    site.pagina.route(lambda url: "/api/v1/santos" in url, lambda rota: rota.abort())
    assert js("""const m = await import('/js/api/cliente.js');
        try { await m.buscarJsonNaApi('/santos'); } catch (e) { return e.codigo; }""") == "FALHA_DE_REDE"


def test_resposta_503_sem_json_vira_SERVICO_INDISPONIVEL(site, js):
    site.pagina.route(lambda url: "/api/v1/santos" in url, lambda rota: rota.fulfill(status=503, body="<html>"))
    assert js("""const m = await import('/js/api/cliente.js');
        try { await m.buscarJsonNaApi('/santos'); } catch (e) { return e.codigo; }""") == "SERVICO_INDISPONIVEL"


def test_cancelamento_vira_AbortError(js):
    assert js("""const m = await import('/js/api/cliente.js');
        const controlador = new AbortController();
        const consulta = m.buscarJsonNaApi('/santos', {}, { signal: controlador.signal });
        controlador.abort();
        try { await consulta; } catch (e) { return [e.name, m.ehCancelamentoDaConsulta(e)]; }""") == ["AbortError", True]


def test_tempo_esgotado_vira_TEMPO_ESGOTADO(site, js):
    site.pagina.route(lambda url: "/api/v1/santos" in url, lambda rota: None)  # nunca responde
    assert js("""const m = await import('/js/api/cliente.js');
        try { await m.buscarJsonNaApi('/santos', {}, { tempoLimite: 200 }); } catch (e) { return e.codigo; }""") == "TEMPO_ESGOTADO"


def test_so_usa_GET(site, js):
    metodos = []
    site.pagina.on("request", lambda requisicao: metodos.append(requisicao.method) if "/api/v1/" in requisicao.url else None)
    js("const m = await import('/js/api/cliente.js'); await m.buscarJsonNaApi('/momentos');")
    assert metodos == ["GET"]


def test_recomendados_sem_ids_nao_chama_a_api(site, js):
    resultado = js("""const m = await import('/js/api/servicos.js');
        try { await m.servicoLivros.listarLivrosRecomendados([]); return 'chamou'; } catch (e) { return 'recusou'; }""")
    assert resultado == "recusou"
    assert not any("recomendados" in url for url in site.chamadas_a_api)


def test_listar_todas_as_paginas_percorre_ate_o_fim(js):
    assert js("""const m = await import('/js/api/servicos.js');
        let chamadas = 0;
        const listar = async ({ pagina }) => { chamadas += 1; return { itens: [pagina], total_paginas: 2 }; };
        return [await m.listarTodasAsPaginas(listar), chamadas];""") == [[1, 2], 2]


def test_mensagens_de_erro_amigaveis(js):
    assert js("""const m = await import('/js/api/erros.js');
        return [m.montarMensagemDeErro({ codigo: 'FALHA_DE_REDE' }, 'os santos').titulo,
                m.ehErroRecuperavel({ codigo: 'RECURSO_NAO_ENCONTRADO' }), m.ehErroRecuperavel({ codigo: 'TEMPO_ESGOTADO' }),
                m.ehErroDeNaoEncontrado({ codigo: 'ROTA_NAO_ENCONTRADA' })];""") \
        == ["Não foi possível carregar os santos no momento.", False, True, True]


def test_escapar_html_impede_codigo_vindo_da_api(js):
    assert js("const m = await import('/js/componentes/html.js'); return m.escaparHtml(`<script>\"x\"&'y'</script>`);") \
        == "&lt;script&gt;&quot;x&quot;&amp;&#39;y&#39;&lt;/script&gt;"


# ---------------------------------------------------------------- estado no navegador (localStorage)
def test_santos_acessados_deduplica_e_poe_o_mais_recente_na_frente(js):
    assert js("""localStorage.clear(); const m = await import('/js/estado/santosAcessados.js');
        m.registrarSantoAcessado(2); m.registrarSantoAcessado(5); m.registrarSantoAcessado(2);
        return m.listarSantosAcessados();""") == [2, 5]


def test_santos_acessados_guarda_no_maximo_20(js):
    assert js("""localStorage.clear(); const m = await import('/js/estado/santosAcessados.js');
        for (let id = 1; id <= 30; id++) m.registrarSantoAcessado(id);
        const lista = m.listarSantosAcessados(); return [lista.length, lista[0]];""") == [20, 30]


def test_santos_acessados_ignora_ids_invalidos_e_dados_corrompidos(js):
    assert js("""localStorage.clear(); const m = await import('/js/estado/santosAcessados.js');
        m.registrarSantoAcessado('abc'); m.registrarSantoAcessado(-1); m.registrarSantoAcessado(1.5);
        const vazio = m.listarSantosAcessados();
        localStorage.setItem('fides:v1:santos-acessados', '{não é json'); const corrompido = m.listarSantosAcessados();
        localStorage.setItem('fides:v1:santos-acessados', JSON.stringify([3, '4', 0, null, 3]));
        return [vazio, corrompido, m.listarSantosAcessados()];""") == [[], [], [3, 4]]


def test_novena_pessoal_normaliza_dias_e_tipos(js):
    assert js("""localStorage.clear(); const a = await import('/js/estado/armazenamento.js'); const m = await import('/js/estado/novenaPessoal.js');
        a.gravarJsonNoDispositivo('novena:1', { marcados: [3, 3, 0, 12, '2', 1], pedidos: 42 });
        return m.lerNovenaPessoal(1);""") == {"marcados": [1, 3], "pedidos": ""}


def test_novena_pessoal_alterna_e_persiste_e_sem_conteudo_remove_a_chave(js):
    assert js("""localStorage.clear(); const m = await import('/js/estado/novenaPessoal.js');
        const gravou = m.salvarNovenaPessoal(7, m.alternarDiaMarcado({ marcados: [], pedidos: '' }, 4)).gravou;
        const marcados = m.lerNovenaPessoal(7).marcados;
        const desmarcados = m.alternarDiaMarcado(m.lerNovenaPessoal(7), 4).marcados;
        m.salvarNovenaPessoal(8, { marcados: [1], pedidos: 'x' }); m.salvarNovenaPessoal(8, { marcados: [], pedidos: '' });
        return [gravou, marcados, desmarcados, localStorage.getItem('fides:v1:novena:8')];""") == [True, [4], [], None]


def test_armazenamento_indisponivel_nao_quebra(js):
    assert js("""const a = await import('/js/estado/armazenamento.js'); const m = await import('/js/estado/novenaPessoal.js');
        const original = Storage.prototype.setItem; Storage.prototype.setItem = () => { throw new Error('QuotaExceededError'); };
        try { return [a.gravarJsonNoDispositivo('x', 1), a.lerJsonDoDispositivo('x', 'padrão'), m.salvarNovenaPessoal(9, { marcados: [1], pedidos: '' }).gravou, a.armazenamentoDisponivel()]; }
        finally { Storage.prototype.setItem = original; }""") == [False, "padrão", False, False]


# ---------------------------------------------------------------- utilitários
def test_paginacao_mostra_atual_mais_ou_menos_2(js):
    assert js("""const m = await import('/js/utils/paginacao.js');
        return [m.calcularPaginasVisiveis(1, 9), m.calcularPaginasVisiveis(5, 9), m.calcularPaginasVisiveis(9, 9), m.calcularPaginasVisiveis(1, 0)];""") \
        == [[1, 2, 3], [3, 4, 5, 6, 7], [7, 8, 9], []]


def test_le_pagina_e_id_da_url_com_seguranca(js):
    assert js("""const m = await import('/js/utils/paginacao.js');
        return [m.lerNumeroDaPagina('abc'), m.lerNumeroDaPagina('0'), m.lerNumeroDaPagina('3'), m.lerIdDaUrl('2'), m.lerIdDaUrl('x'), m.lerIdDaUrl('1.5')];""") \
        == [1, 1, 3, 2, None, None]


def test_datas_sem_problema_de_fuso(js):
    assert js("""const m = await import('/js/utils/datas.js');
        return [m.ehDataIso('2026-11-05'), m.ehDataIso('2026-02-30'), m.somarDias('2026-11-30', 1), m.escreverDataCurta('2026-11-05'),
                m.escreverDataPorExtenso('2026-11-05')];""") \
        == [True, False, "2026-12-01", "05/11", "Quinta-feira, 5 de novembro de 2026"]


def test_data_dentro_do_periodo_da_api(js):
    assert js("""const m = await import('/js/utils/datas.js'); const periodo = { hoje: '2026-11-05', inicio: '2026-10-29', fim: '2026-11-12' };
        return [m.dataDentroDoPeriodo('2026-11-12', periodo), m.dataDentroDoPeriodo('2026-11-13', periodo)];""") == [True, False]


def test_situacao_da_agenda_da_novena(js):
    assert js("""const m = await import('/js/utils/novena.js');
        const agendada = m.descreverAgendaDaNovena({ situacao: 'agendada', dia_atual: 0, data_inicio: '2026-11-07' }, 9);
        return [m.descreverAgendaDaNovena({ situacao: 'em_andamento', dia_atual: 5, data_inicio: '2026-11-01' }, 9).texto,
                agendada.tipo, agendada.texto.includes('Dia 0'), agendada.texto.includes('7 de novembro'),
                m.descreverAgendaDaNovena(null).tipo, m.escolherDiaInicial(null), m.escolherDiaInicial({ situacao: 'em_andamento', dia_atual: 4 }),
                m.escolherDiaInicial({ situacao: 'agendada', dia_atual: 0 })];""") \
        == ["Dia 5 de 9", "agendada", False, True, "sem_agenda", 1, 4, 1]


def test_liturgia_das_horas_em_ordem_canonica(js):
    assert js("""const m = await import('/js/utils/liturgia.js');
        return m.ordenarHorasDaLiturgia([{ bloco: { codigo: 'vesperas' } }, { bloco: { codigo: 'laudes' } }, { bloco: { codigo: 'horas_medias' } }]).map((h) => h.bloco.codigo);""") \
        == ["laudes", "horas_medias", "vesperas"]

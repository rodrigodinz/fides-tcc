// Peças visuais reaproveitadas pelas páginas. Cada função devolve um TEXTO de HTML com as classes do CSS; a página junta esses textos e coloca na tela com innerHTML.
import { escaparHtml, gerarId } from "./html.js";
import { icone } from "./icones.js";
import { montarUrlDaImagem } from "../api/cliente.js";
import { montarMensagemDeErro, ehErroRecuperavel } from "../api/erros.js";
import { enderecos } from "../utils/enderecos.js";
import { escreverDataCurta, escreverDataPorExtenso, somarDias } from "../utils/datas.js";
import { descreverAgendaDaNovena } from "../utils/novena.js";
import { calcularPaginasVisiveis } from "../utils/paginacao.js";

const juntarClasses = (...classes) => classes.filter(Boolean).join(" ");

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- ornamentos +-+-+-+-+-+-+-+-+-+-+-+-+-+-
const Arquivos_Dos_Ornamentos = {
  crista: "/imagens/ornamentos/crista-acanto-familia-b.svg",
  titulo: "/imagens/ornamentos/titulo-familia-b.svg",
  divisor: "/imagens/ornamentos/divisor-familia-a.svg",
  curto: "/imagens/ornamentos/divisor-curto-familia-a.svg",
};
const Dimensoes_Dos_Ornamentos = { crista: [372, 60], titulo: [516, 40], divisor: [464, 26], curto: [200, 20] };
const Classes_Dos_Ornamentos = {
  crista: "ornamento-crista",
  titulo: "ornamento-de-titulo",
  divisor: "ornamento-divisor",
  curto: "ornamento-divisor-curto",
};

// ornamentos dourados são só decoração
export function ornamento(tipo = "divisor", classe = "") {
  const [largura, altura] = Dimensoes_Dos_Ornamentos[tipo];
  return `<img class="${`ornamento ${Classes_Dos_Ornamentos[tipo]} ${classe}`.trim()}" src="${Arquivos_Dos_Ornamentos[tipo]}" width="${largura}" height="${altura}" alt="" aria-hidden="true">`;
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- botões +-+-+-+-+-+-+-+-+-+-+-+-+-+-
const Classes_Das_Variantes_Do_Botao = {
  primario: "botao-primario",
  secundario: "botao-secundario",
  especial: "botao-especial",
  texto: "botao-de-texto",
};
const montarClassesDoBotao = (variante, pequeno, classe) =>
  `botao ${Classes_Das_Variantes_Do_Botao[variante]}${pequeno ? " botao-pequeno" : ""} ${classe}`.trim();

// variante muda a cor: primario, secundario, especial ou texto; "atributos" recebe extras como data-acao="..."
export function botao({ texto, variante = "primario", icone: nomeDoIcone, iconeDepois, pequeno, classe = "", atributos = "" }) {
  return `<button type="button" class="${montarClassesDoBotao(variante, pequeno, classe)}" ${atributos}>${nomeDoIcone ? icone(nomeDoIcone) : ""}${escaparHtml(texto)}${iconeDepois ? icone(iconeDepois) : ""}</button>`;
}

// mesmo visual do botão, mas é um link para outra página
export function botaoLink({ texto, para, variante = "primario", icone: nomeDoIcone, iconeDepois, pequeno, classe = "" }) {
  return `<a class="${montarClassesDoBotao(variante, pequeno, classe)}" href="${para}">${nomeDoIcone ? icone(nomeDoIcone) : ""}${escaparHtml(texto)}${iconeDepois ? icone(iconeDepois) : ""}</a>`;
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- cards +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// Destaque = card dourado, Simples = sem moldura;
export function card({ titulo, nivel = 3, para, rotulo, meta, corpo = "", acoes, destaque, simples, classe = "" }) {
  const tagDoTitulo = `h${nivel}`;
  const tituloDoCard = titulo
    ? `<${tagDoTitulo} class="titulo-do-card"${rotulo ? ' style="margin-top:4px"' : ""}>${para ? `<a class="link-que-cobre-o-card" href="${para}">${escaparHtml(titulo)}</a>` : escaparHtml(titulo)}</${tagDoTitulo}>`
    : "";
  return `<article class="${juntarClasses("card", destaque && "card-de-destaque", simples && "card-simples", classe)}">`
    + (destaque ? '<span class="cantos-ornamentais-do-card" aria-hidden="true"></span>' : "")
    + (rotulo ? `<p class="rotulo-pequeno">${escaparHtml(rotulo)}</p>` : "")
    + tituloDoCard
    + (meta ? `<p class="texto-auxiliar informacoes-do-card">${escaparHtml(meta)}</p>` : "")
    + corpo
    + (acoes ? `<div class="botoes-do-card acima-do-link-do-card">${acoes}</div>` : "")
    + "</article>";
}

// foto do santo. se a imagem não carregar, aparece o símbolo do Fides
export function retratoDoSanto({ fotoUrl, nome, decorativo = false, classe = "", carregamento = "lazy" }) {
  const urlDaImagem = montarUrlDaImagem(fotoUrl);
  const conteudo = urlDaImagem
    ? `<img src="${escaparHtml(urlDaImagem)}" alt="${decorativo ? "" : `Retrato de ${escaparHtml(nome)}`}" width="400" height="500" loading="${carregamento}" decoding="async" data-retrato-de="${escaparHtml(nome)}" data-decorativo="${decorativo}">`
    : retratoIndisponivel(nome, decorativo);
  return `<div class="${`retrato ${classe}`.trim()}">${conteudo}</div>`;
}

export function retratoIndisponivel(nome, decorativo) {
  const acessibilidade = decorativo ? "" : ` role="img" aria-label="Retrato de ${escaparHtml(nome)} não disponível"`;
  return `<div class="retrato-indisponivel"${acessibilidade}><img src="/imagens/simbolo-fides.svg" alt="" width="44" height="57"><span aria-hidden="true">Retrato não disponível</span></div>`;
}

// card do santo com a foto do santo, o link no nome cobre o card inteiro
export function cardDoSanto(santo, nivel = 3) {
  return `<article class="card card-do-santo">${retratoDoSanto({ fotoUrl: santo.foto_url, nome: santo.nome, decorativo: true })}`
    + `<div class="corpo-do-card-do-santo"><h${nivel} class="nome-no-card-do-santo"><a class="link-que-cobre-o-card" href="${enderecos.santo(santo.id)}">${escaparHtml(santo.nome)}</a></h${nivel}>`
    + `<span class="ver-mais-no-card-do-santo" aria-hidden="true">Ver vida e devoções ${icone("direita")}</span></div></article>`;
}

// card da novena, em andamento fica destacada e botão para ler o dia atual
export function cardDaNovena(novena, nivel = 2) {
  const situacaoDaAgenda = descreverAgendaDaNovena(novena.agenda, novena.total_dias);
  const novenaEmAndamento = situacaoDaAgenda.tipo === "em_andamento";
  const informacoesDoCard = [novena.santo?.nome, situacaoDaAgenda.tipo === "agendada" ? situacaoDaAgenda.texto : null].filter(Boolean).join(" · ");
  return card({
    destaque: novenaEmAndamento, nivel, titulo: novena.titulo, para: enderecos.novena(novena.id),
    rotulo: novenaEmAndamento ? `${situacaoDaAgenda.rotulo} · ${situacaoDaAgenda.texto}` : situacaoDaAgenda.rotulo,
    meta: informacoesDoCard || null,
    acoes: novenaEmAndamento
      ? botaoLink({ variante: "especial", texto: `Ler o dia ${situacaoDaAgenda.diaAtual}`, para: enderecos.novena(novena.id, situacaoDaAgenda.diaAtual) })
      : null,
    corpo: novena.descricao ? `<p class="texto-do-card">${escaparHtml(novena.descricao)}</p>` : "",
  });
}

const Tamanho_De_Texto_Longo = 220;

// card da oração
export function cardDaOracao(oracao, nivel = 3) {
  const idDoTexto = gerarId("oracao");
  const textoLongo = oracao.texto.length > Tamanho_De_Texto_Longo;
  const informacoesDaOracao = [oracao.basica ? "Oração básica" : null, oracao.santo?.nome].filter(Boolean).join(" · ");
  const temMomentos = oracao.momentos?.length > 0;
  let rodape = "";
  if (textoLongo || temMomentos) {
    const etiquetas = temMomentos
      ? `<ul class="lista-de-etiquetas" aria-label="Momentos do dia">${oracao.momentos.map((momento) => `<li class="etiqueta">${escaparHtml(momento.nome)}</li>`).join("")}</ul>`
      : "<span></span>";
    const botaoAbrir = textoLongo
      ? botao({ variante: "texto", pequeno: true, texto: "Ler a oração inteira", atributos: `aria-expanded="false" aria-controls="${idDoTexto}" data-alternar-oracao` })
      : "";
    rodape = `<div class="rodape-da-oracao">${etiquetas}${botaoAbrir}</div>`;
  }
  return card({
    simples: true, titulo: oracao.titulo, nivel, meta: informacoesDaOracao || null, classe: "oracao",
    corpo: `<p id="${idDoTexto}" class="texto-da-oracao texto-com-quebras-de-linha${textoLongo ? " texto-da-oracao-recolhido" : ""}">${escaparHtml(oracao.texto)}</p>${rodape}`,
  });
}

export function ligarCardsDeOracao(container) {
  container.querySelectorAll("[data-alternar-oracao]").forEach((botaoDaOracao) => {
    botaoDaOracao.addEventListener("click", () => {
      const textoDaOracao = document.getElementById(botaoDaOracao.getAttribute("aria-controls"));
      const vaiAbrir = botaoDaOracao.getAttribute("aria-expanded") !== "true";
      botaoDaOracao.setAttribute("aria-expanded", String(vaiAbrir));
      botaoDaOracao.textContent = vaiAbrir ? "Recolher" : "Ler a oração inteira";
      textoDaOracao.classList.toggle("texto-da-oracao-recolhido", !vaiAbrir);
    });
  });
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- estados da consulta +-+-+-+-+-+-+-+-+-+-+-+-+-+-
const Classes_Dos_Tipos_De_Alerta = {
  erro: "alerta-de-erro",
  aviso: "alerta-de-aviso",
  sucesso: "alerta-de-sucesso",
  info: "alerta-de-informacao",
};

export function alerta({ tipo = "info", titulo, corpo = "", acoes, papel }) {
  const nomeDoIcone = tipo === "erro" ? "alerta" : tipo === "sucesso" ? "check" : "info";
  const papelAcessivel = papel ?? (tipo === "erro" ? "alert" : "status");
  return `<div class="alerta ${Classes_Dos_Tipos_De_Alerta[tipo]}" role="${papelAcessivel}">${icone(nomeDoIcone)}<div>`
    + (titulo ? `<strong class="titulo-do-alerta">${escaparHtml(titulo)}</strong>` : "")
    + corpo
    + (acoes ? `<div class="botoes-do-alerta">${acoes}</div>` : "")
    + "</div></div>";
}

// mensagem de erro amigável, como pede a RNF, "Tentar novamente" só aparece com os erros que podem passar sem dar uma mensagem de erro diferente (como 404, 500, etc)
// o botão tem data-acao="tentar-novamente": quem desenha o erro liga o clique com ligarTentarNovamente()
export function mensagemDeErro({ erro, conteudoBuscado, comTentarNovamente = true, acaoExtra = "" }) {
  const { titulo, texto } = montarMensagemDeErro(erro, conteudoBuscado);
  const podeTentarNovamente = comTentarNovamente && ehErroRecuperavel(erro);
  const acoes = podeTentarNovamente || acaoExtra
    ? `${podeTentarNovamente ? botao({ variante: "secundario", icone: "recarregar", texto: "Tentar novamente", atributos: 'data-acao="tentar-novamente"' }) : ""}${acaoExtra}`
    : null;
  return alerta({ tipo: "erro", titulo, acoes, corpo: `<p>${escaparHtml(texto)}</p>` });
}

export function ligarTentarNovamente(container, funcao) {
  container.querySelectorAll('[data-acao="tentar-novamente"]').forEach((botaoTentar) => botaoTentar.addEventListener("click", funcao));
}

// quando a busca deu certo mas não dá resultados (não é um erro, só não tem nada pra mostrar mesmo, a busca volta vazia)
export function mensagemDeListaVazia({ titulo, texto, acao }) {
  return `<div class="mensagem-sem-conteudo" role="status">${ornamento("curto")}<h3 class="subtitulo-menor">${escaparHtml(titulo)}</h3>`
    + (texto ? `<p class="texto-auxiliar">${escaparHtml(texto)}</p>` : "")
    + (acao ? `<div class="botoes-da-mensagem-sem-conteudo">${acao}</div>` : "")
    + "</div>";
}

export function mensagemDeNaoEncontrado({ titulo = "Conteúdo não encontrado", voltar }) {
  return `<div class="mensagem-sem-conteudo">${ornamento("curto")}<h2 class="subtitulo">${escaparHtml(titulo)}</h2>`
    + '<p class="texto-auxiliar">O endereço pode estar incorreto ou o conteúdo não existe mais.</p>'
    + (voltar ? `<div class="botoes-da-mensagem-sem-conteudo">${botaoLink({ variante: "secundario", icone: "esquerda", para: voltar.para, texto: voltar.texto })}</div>` : "")
    + "</div>";
}

export function carregando({ tipo = "cards", quantidade = 3, texto = "Carregando…" } = {}) {
  const posicoes = Array.from({ length: quantidade }, (_, posicao) => posicao);
  let blocosCarregando;
  if (tipo === "texto") {
    blocosCarregando = '<div class="largura-de-leitura" style="display:grid;gap:10px"><span class="bloco-carregando" style="height:26px;width:55%"></span>'
      + posicoes.map((posicao) => `<span class="bloco-carregando" style="height:14px;width:${92 - posicao * 9}%"></span>`).join("") + "</div>";
  } else if (tipo === "santos") {
    blocosCarregando = `<div class="grade grade-de-3-colunas">${posicoes.map(() => '<span class="bloco-carregando bloco-carregando-retrato"></span>').join("")}</div>`;
  } else {
    blocosCarregando = `<div class="grade grade-de-2-colunas">${posicoes.map(() => '<span class="bloco-carregando bloco-carregando-card"></span>').join("")}</div>`;
  }
  return `<div aria-busy="true" role="status"><span class="somente-para-leitor-de-tela">${escaparHtml(texto)}</span>${blocosCarregando}</div>`;
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- estrutura das páginas +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// título da página com o ornamento dourado em cima
export function cabecalhoDaPagina({ titulo, rotulo, textoDeAbertura, ornamento: tipoDoOrnamento = "titulo", extra = "" }) {
  return `<header class="cabecalho-da-pagina">${tipoDoOrnamento ? ornamento(tipoDoOrnamento) : ""}`
    + (rotulo ? `<span class="rotulo-pequeno">${escaparHtml(rotulo)}</span>` : "")
    + `<h1 class="titulo-da-pagina">${escaparHtml(titulo)}</h1>`
    + (textoDeAbertura ? `<p class="texto-de-abertura-do-cabecalho">${escaparHtml(textoDeAbertura)}</p>` : "")
    + extra + "</header>";
}

export function tituloDeSecao({ titulo, id, descricao, acao = "", nivel = 2 }) {
  return `<div class="cabecalho-da-secao">${ornamento("curto")}<div class="linha-do-cabecalho-da-secao">`
    + `<h${nivel} class="${nivel === 2 ? "titulo-de-secao" : "subtitulo"}"${id ? ` id="${id}"` : ""}>${escaparHtml(titulo)}</h${nivel}>${acao}</div>`
    + (descricao ? `<p class="texto-auxiliar">${escaparHtml(descricao)}</p>` : "")
    + "</div>";
}

// trilha do início dos dias da novena
export function caminhoDeNavegacao(itens) {
  const itensDoCaminho = itens.map((item, posicao) => {
    const ehUltimoItem = posicao === itens.length - 1;
    return item.para && !ehUltimoItem
      ? `<li><a href="${item.para}">${escaparHtml(item.texto)}</a></li>`
      : `<li><span${ehUltimoItem ? ' aria-current="page"' : ""}>${escaparHtml(item.texto)}</span></li>`;
  }).join("");
  return `<nav class="caminho-de-navegacao" aria-label="Você está em"><ol>${itensDoCaminho}</ol></nav>`;
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- paginação +-+-+-+-+-+-+-+-+-+-+-+-+-+-
export function paginacao({ pagina, totalPaginas, totalRegistros, rotulo = "Paginação" }) {
  if (!totalPaginas || totalPaginas <= 1) return "";
  const botoesDasPaginas = calcularPaginasVisiveis(pagina, totalPaginas).map((numeroDaPagina) =>
    `<li><button type="button" class="botao-de-pagina"${numeroDaPagina === pagina ? ' aria-current="page"' : ""} aria-label="Página ${numeroDaPagina}" data-pagina="${numeroDaPagina}">${numeroDaPagina}</button></li>`).join("");
  return `<nav class="paginacao" aria-label="${escaparHtml(rotulo)}"><ol>`
    + `<li><button type="button" class="botao-de-pagina botao-de-pagina-com-seta"${pagina <= 1 ? " disabled" : ""} aria-label="Página anterior" data-pagina="${pagina - 1}">${icone("esquerda")}<span>Anterior</span></button></li>`
    + botoesDasPaginas
    + `<li><button type="button" class="botao-de-pagina botao-de-pagina-com-seta"${pagina >= totalPaginas ? " disabled" : ""} aria-label="Próxima página" data-pagina="${pagina + 1}"><span>Próxima</span>${icone("direita")}</button></li>`
    + "</ol>"
    + (typeof totalRegistros === "number"
      ? `<p class="texto-auxiliar resumo-da-paginacao">Página ${pagina} de ${totalPaginas} · ${totalRegistros} ${totalRegistros === 1 ? "item" : "itens"}</p>`
      : "")
    + "</nav>";
}

export function ligarPaginacao(container, aoMudarPagina) {
  container.querySelectorAll(".paginacao [data-pagina]").forEach((botaoDaPagina) => {
    botaoDaPagina.addEventListener("click", () => {
      if (botaoDaPagina.getAttribute("aria-current") === "page") return;
      aoMudarPagina(Number(botaoDaPagina.dataset.pagina));
    });
  });
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- calendário da data (liturgia e agenda) +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// dia anterior, calendário, próximo dia
export function seletorDeData({ data, periodo }) {
  if (!periodo) return "";
  const idDoCampo = gerarId("data");
  const diaAnterior = somarDias(data, -1);
  const proximoDia = somarDias(data, 1);
  const voltarParaHoje = data !== periodo.hoje
    ? ' <button type="button" class="botao botao-de-texto botao-pequeno" data-ir-para-data="' + periodo.hoje + '">Voltar para hoje</button>'
    : "";
  return '<div class="seletor-de-data">'
    + botao({ variante: "secundario", icone: "esquerda", texto: escreverDataCurta(diaAnterior), atributos: `${diaAnterior < periodo.inicio ? "disabled" : ""} aria-label="Dia anterior (${escreverDataCurta(diaAnterior)})" data-ir-para-data="${diaAnterior}"` })
    + `<div class="campo-de-formulario"><label for="${idDoCampo}">Escolher data</label><input id="${idDoCampo}" class="caixa-de-texto" type="date" value="${data}" min="${periodo.inicio}" max="${periodo.fim}" data-campo-de-data></div>`
    + botao({ variante: "secundario", iconeDepois: "direita", texto: escreverDataCurta(proximoDia), atributos: `${proximoDia > periodo.fim ? "disabled" : ""} aria-label="Próximo dia (${escreverDataCurta(proximoDia)})" data-ir-para-data="${proximoDia}"` })
    + `<p class="texto-auxiliar periodo-disponivel">Período disponível: ${escreverDataCurta(periodo.inicio)} a ${escreverDataCurta(periodo.fim)} (hoje ± 7 dias).${voltarParaHoje}</p>`
    + "</div>";
}

export function ligarSeletorDeData(container, aoMudarData) {
  container.querySelectorAll("[data-ir-para-data]").forEach((botaoDeData) =>
    botaoDeData.addEventListener("click", () => aoMudarData(botaoDeData.dataset.irParaData)));
  container.querySelectorAll("[data-campo-de-data]").forEach((campoDeData) =>
    campoDeData.addEventListener("change", () => { if (campoDeData.value) aoMudarData(campoDeData.value); }));
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- calendário da novena +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// Os 9 dias em círculos. Cada dia pode estar entre hoje (agenda), marcado (rezado neste aparelho) ou selecionado (aberto na tela)
export function calendarioDaNovena({ novenaId, dias, diaAtual, marcados = [], diaSelecionado, comLegenda = true }) {
  const itensDoCalendario = dias.map((dia) => {
    const ehHoje = diaAtual === dia.numero_do_dia;
    const estaMarcado = marcados.includes(dia.numero_do_dia);
    const estaSelecionado = diaSelecionado === dia.numero_do_dia;
    const descricaoAcessivel = [
      `Dia ${dia.numero_do_dia}`,
      dia.data ? escreverDataCurta(dia.data) : null,
      ehHoje ? "dia atual da agenda" : null,
      estaMarcado ? "marcado como rezado neste dispositivo" : null,
      estaSelecionado ? "aberto" : null,
    ].filter(Boolean).join(", ");
    return `<li class="${juntarClasses("dia-do-calendario", ehHoje && "dia-de-hoje", estaMarcado && "dia-marcado", estaSelecionado && "dia-selecionado")}">`
      + `<a class="circulo-do-dia" href="${enderecos.novena(novenaId, dia.numero_do_dia)}" aria-label="${descricaoAcessivel}"${estaSelecionado ? ' aria-current="step"' : ""}>${dia.numero_do_dia}</a>`
      + `<span class="data-do-dia" aria-hidden="true">${dia.data ? escreverDataCurta(dia.data) : "—"}</span>`
      + `<span class="aviso-de-hoje" aria-hidden="true">${ehHoje ? "Hoje" : ""}</span></li>`;
  }).join("");
  const legenda = comLegenda
    ? '<ul class="legenda-do-calendario" aria-label="Legenda"><li><i class="amostra-do-dia amostra-do-dia-de-hoje"></i>Dia atual (agenda da novena)</li><li><i class="amostra-do-dia amostra-do-dia-rezado"></i>Rezado (marcado neste dispositivo)</li><li><i class="amostra-do-dia amostra-do-dia-aberto"></i>Dia aberto</li><li><i class="amostra-do-dia"></i>Demais dias</li></ul>'
    : "";
  return `<ol class="calendario-da-novena" aria-label="Os nove dias da novena">${itensDoCalendario}</ol>${legenda}`;
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- campos de formulário +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// campo de busca. O botão de limpar só aparece quando tem texto na página (a página controla com hidden)
export function campoDeBuscaComBotaoDeLimpar({ rotulo, valor = "", placeholder = "", ajuda, id }) {
  const idDoCampo = id ?? gerarId("busca");
  return `<div class="campo-de-formulario"><label for="${idDoCampo}">${escaparHtml(rotulo)}</label><div class="campo-de-busca" role="search">${icone("lupa")}`
    + `<input id="${idDoCampo}" class="caixa-de-texto" type="search" value="${escaparHtml(valor)}" placeholder="${escaparHtml(placeholder)}" autocomplete="off" spellcheck="false"${ajuda ? ` aria-describedby="${idDoCampo}-ajuda"` : ""}>`
    + `<button type="button" class="botao-de-icone botao-de-limpar-a-busca" aria-label="Limpar busca" data-limpar-busca${valor ? "" : " hidden"}>${icone("fechar")}</button></div>`
    + (ajuda ? `<span id="${idDoCampo}-ajuda" class="texto-auxiliar">${escaparHtml(ajuda)}</span>` : "")
    + "</div>";
}

// select que a gente usou nos filtros por santo e por tipo
export function seletor({ rotulo, valor = "", opcoes, textoDeTodos = "Todos", desabilitado, id }) {
  const idDoCampo = id ?? gerarId("selecao");
  const opcoesDoSeletor = opcoes.map((opcao) =>
    `<option value="${escaparHtml(opcao.valor)}"${String(opcao.valor) === String(valor) ? " selected" : ""}>${escaparHtml(opcao.rotulo)}</option>`).join("");
  return `<div class="campo-de-formulario"><label for="${idDoCampo}">${escaparHtml(rotulo)}</label>`
    + `<select id="${idDoCampo}" class="caixa-de-selecao"${desabilitado ? " disabled" : ""}><option value="">${escaparHtml(textoDeTodos)}</option>${opcoesDoSeletor}</select></div>`;
}

// botões liga/desliga (momentos do dia)
export function grupoDeOpcoes({ rotulo, valor = "", opcoes }) {
  const idDoRotulo = gerarId("opcoes");
  const botoesDasOpcoes = opcoes.map((opcao) => {
    const opcaoEstaLigada = String(valor) === String(opcao.valor);
    return `<button type="button" class="botao-de-opcao" aria-pressed="${opcaoEstaLigada}" data-valor="${escaparHtml(opcao.valor)}">${opcao.icone ? icone(opcao.icone) : ""}${escaparHtml(opcao.rotulo)}</button>`;
  }).join("");
  return `<div class="campo-de-formulario"><span class="rotulo-do-campo" id="${idDoRotulo}">${escaparHtml(rotulo)}</span>`
    + `<div class="grupo-de-opcoes" role="group" aria-labelledby="${idDoRotulo}">${botoesDasOpcoes}</div></div>`;
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- liturgia +-+-+-+-+-+-+-+-+-+-+-+-+-+-
const Abas_Da_Liturgia = [
  { para: "/liturgia.html", montarEndereco: enderecos.liturgiaDoDia, nome: "Liturgia do Dia", icone: "liturgia" },
  { para: "/liturgia-horas.html", montarEndereco: enderecos.liturgiaDasHoras, nome: "Liturgia das Horas", icone: "horas" },
];

// abas Liturgia do Dia / Liturgia das Horas, levando junto a data escolhida
export function abasDaLiturgia(data) {
  const abas = Abas_Da_Liturgia.map((aba) =>
    `<li><a class="aba" href="${aba.montarEndereco(data)}"${window.location.pathname === aba.para ? ' aria-current="page"' : ""}>${icone(aba.icone)}${aba.nome}</a></li>`).join("");
  return `<nav aria-label="Liturgia"><ul class="abas">${abas}</ul></nav>`;
}

export function avisoDemonstracao(texto) {
  return alerta({ tipo: "aviso", titulo: "Conteúdo de demonstração", papel: "note", corpo: `<p>${escaparHtml(texto)}</p>` });
}

const Codigos_De_Erro_De_Data = ["DATA_FORA_DO_INTERVALO", "LITURGIA_NAO_CADASTRADA", "PARAMETRO_INVALIDO"];

// erros de data (fora do período, sem liturgia) oferecem "Ir para hoje" em vez de "Tentar novamente"
export function erroDeData(erro) {
  const { titulo, texto } = montarMensagemDeErro(erro);
  if (Codigos_De_Erro_De_Data.includes(erro?.codigo)) {
    const dataInvalida = erro.codigo === "PARAMETRO_INVALIDO";
    return alerta({
      tipo: "info", titulo: dataInvalida ? "Data inválida." : titulo,
      acoes: botao({ variante: "secundario", icone: "calendario", texto: "Ir para hoje", atributos: 'data-acao="ir-para-hoje"' }),
      corpo: `<p>${escaparHtml(dataInvalida ? "Use uma data no formato do calendário." : texto)}</p>`,
    });
  }
  return alerta({
    tipo: "erro", titulo,
    acoes: botao({ variante: "secundario", icone: "recarregar", texto: "Tentar novamente", atributos: 'data-acao="tentar-novamente"' }),
    corpo: `<p>${escaparHtml(texto)}</p>`,
  });
}

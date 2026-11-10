// Orações com filtros combináveis (momento do dia, santo e tipo). Todos os filtros ficam na URL:
// oracoes.html?momento=4&santo=2&tipo=basicas&pagina=2
import { montarLayout } from "../layout.js";
import { servicoOracoes, servicoSantos, listarTodasAsPaginas } from "../api/servicos.js";
import { criarConsulta, paginaEstaVazia } from "../utils/consulta.js";
import { lerParametrosDaUrl, atualizarParametrosDaUrl, aoMudarParametrosDaUrl } from "../utils/url.js";
import { lerIdDaUrl, lerNumeroDaPagina } from "../utils/paginacao.js";
import { Nomes_Dos_Icones } from "../componentes/icones.js";
import {
  alerta, botao, card, cardDaOracao, carregando, grupoDeOpcoes, mensagemDeErro, mensagemDeListaVazia, ligarCardsDeOracao, ligarPaginacao,
  ligarTentarNovamente, paginacao, seletor,
} from "../componentes/componentes.js";

montarLayout();

const Tipos_De_Oracao = [{ valor: "basicas", rotulo: "Só orações básicas" }, { valor: "outras", rotulo: "Demais orações" }];
const areaDoDestaque = document.getElementById("destaque-basicas");
const areaDosFiltros = document.getElementById("filtros");
const areaDasOracoes = document.getElementById("lista-de-oracoes");
const consultarOracoes = criarConsulta();

// listas que enchem os filtros; null = ainda carregando; "erro" = não carregou
let momentosDoDia = null;
let santosDoFiltro = null;
let textoDaContagem = " ";
let erroDosMomentos = null;

// lê os filtros atuais da URL (valores inválidos são ignorados)
function lerFiltros() {
  const parametrosDaUrl = lerParametrosDaUrl();
  const tipoNaUrl = parametrosDaUrl.get("tipo");
  const tipo = ["basicas", "outras"].includes(tipoNaUrl) ? tipoNaUrl : "";
  const filtros = {
    momento: lerIdDaUrl(parametrosDaUrl.get("momento")),
    santo: lerIdDaUrl(parametrosDaUrl.get("santo")),
    tipo,
    pagina: lerNumeroDaPagina(parametrosDaUrl.get("pagina")),
    basica: tipo === "basicas" ? true : tipo === "outras" ? false : undefined,
  };
  filtros.temFiltroAtivo = Boolean(filtros.momento || filtros.santo || filtros.tipo);
  return filtros;
}

// trocar qualquer filtro volta para a página 1
function definirFiltro(nomeDoFiltro, valorDoFiltro) {
  const parametrosDaUrl = lerParametrosDaUrl();
  if (valorDoFiltro) parametrosDaUrl.set(nomeDoFiltro, valorDoFiltro); else parametrosDaUrl.delete(nomeDoFiltro);
  parametrosDaUrl.delete("pagina");
  atualizarParametrosDaUrl(parametrosDaUrl, { substituir: true });
  atualizarTela();
}

function limparFiltros() {
  atualizarParametrosDaUrl(new URLSearchParams(), { substituir: true });
  atualizarTela();
}

function irParaPagina(numeroDaPagina) {
  const parametrosDaUrl = lerParametrosDaUrl();
  parametrosDaUrl.set("pagina", String(numeroDaPagina));
  atualizarParametrosDaUrl(parametrosDaUrl);
  carregarOracoes();
}

// card dourado "Orações básicas": só aparece quando nenhum filtro está ligado
function desenharDestaque() {
  const filtros = lerFiltros();
  areaDoDestaque.innerHTML = filtros.tipo !== "basicas" && !filtros.temFiltroAtivo
    ? `<div class="secao">${card({
      destaque: true, titulo: "Orações básicas", rotulo: "Para começar", nivel: 2,
      acoes: botao({ variante: "primario", texto: "Ver orações básicas", atributos: "data-ver-basicas" }),
      corpo: '<p class="texto-do-card">As orações mais conhecidas e rezadas, reunidas em um só lugar.</p>',
    })}</div>`
    : "";
  areaDoDestaque.querySelector("[data-ver-basicas]")?.addEventListener("click", () => definirFiltro("tipo", "basicas"));
}

// Os filtros são redesenhados a cada busca (para atualizar a contagem). Para a pessoa não perder
// o lugar onde estava no teclado, guardamos a posição do controle focado e devolvemos o foco depois.
function desenharFiltros() {
  const controlesAntes = [...areaDosFiltros.querySelectorAll("button, select")];
  const posicaoDoFoco = controlesAntes.indexOf(document.activeElement);
  desenharControlesDosFiltros();
  if (posicaoDoFoco >= 0) areaDosFiltros.querySelectorAll("button, select")[posicaoDoFoco]?.focus();
}

function desenharControlesDosFiltros() {
  const filtros = lerFiltros();
  // cada momento do dia vira um botão de opção; o ícone é o do código do momento (ao_acordar, missa...)
  const opcoesDosMomentos = momentosDoDia === "erro"
    ? mensagemDeErro({ erro: erroDosMomentos, conteudoBuscado: "os momentos do dia" })
    : grupoDeOpcoes({
      rotulo: "Momento do dia", valor: filtros.momento ?? "",
      opcoes: (momentosDoDia ?? []).map((momento) => ({ valor: momento.id, rotulo: momento.nome, icone: Nomes_Dos_Icones.includes(momento.codigo) ? momento.codigo : undefined })),
    });
  const avisoDoFiltroDeSanto = santosDoFiltro === "erro"
    ? `<div style="margin-top:12px">${alerta({ tipo: "info", titulo: "Filtro por santo indisponível", corpo: "Não foi possível carregar a lista de santos agora." })}</div>`
    : "";
  const opcoesDeSanto = Array.isArray(santosDoFiltro) ? santosDoFiltro.map((santo) => ({ valor: santo.id, rotulo: santo.nome })) : [];

  areaDosFiltros.innerHTML = '<h2 id="titulo-dos-filtros" class="somente-para-leitor-de-tela">Filtros</h2>'
    + opcoesDosMomentos
    + '<div class="filtros" style="margin-top:20px">'
    + seletor({ rotulo: "Santo", valor: filtros.santo ?? "", opcoes: opcoesDeSanto, textoDeTodos: "Todos os santos", desabilitado: !Array.isArray(santosDoFiltro) })
    + seletor({ rotulo: "Tipo", valor: filtros.tipo, opcoes: Tipos_De_Oracao, textoDeTodos: "Todas as orações" })
    + "</div>"
    + avisoDoFiltroDeSanto
    + `<div class="rodape-dos-filtros"><p class="texto-auxiliar" role="status">${textoDaContagem}</p>`
    + (filtros.temFiltroAtivo ? botao({ variante: "secundario", pequeno: true, icone: "fechar", texto: "Limpar filtros", atributos: "data-limpar-filtros" }) : "")
    + "</div>";

  // clicar no botão de opção ligado desliga o filtro (por isso o valor vira "")
  areaDosFiltros.querySelectorAll(".botao-de-opcao").forEach((botaoDeOpcao) => botaoDeOpcao.addEventListener("click", () =>
    definirFiltro("momento", botaoDeOpcao.getAttribute("aria-pressed") === "true" ? "" : botaoDeOpcao.dataset.valor)));
  const [seletorDeSanto, seletorDeTipo] = areaDosFiltros.querySelectorAll("select");
  seletorDeSanto.addEventListener("change", () => definirFiltro("santo", seletorDeSanto.value));
  seletorDeTipo.addEventListener("change", () => definirFiltro("tipo", seletorDeTipo.value));
  areaDosFiltros.querySelector("[data-limpar-filtros]")?.addEventListener("click", limparFiltros);
  ligarTentarNovamente(areaDosFiltros, carregarMomentos);
}

async function carregarMomentos() {
  momentosDoDia = null;
  desenharFiltros();
  try {
    momentosDoDia = await servicoOracoes.listarMomentosDoDia();
  } catch (erro) {
    erroDosMomentos = erro;
    momentosDoDia = "erro";
  }
  desenharFiltros();
}

async function carregarSantosDoFiltro() {
  try {
    santosDoFiltro = await listarTodasAsPaginas((filtros, opcoes) => servicoSantos.listarSantos(filtros, opcoes));
  } catch {
    santosDoFiltro = "erro";
  }
  desenharFiltros();
}

async function carregarOracoes() {
  const filtros = lerFiltros();
  areaDasOracoes.setAttribute("aria-busy", "true");
  areaDasOracoes.innerHTML = carregando({ quantidade: 4, texto: "Carregando orações…" });
  textoDaContagem = " ";
  desenharFiltros();
  const resultado = await consultarOracoes(
    (signal) => servicoOracoes.listarOracoes(
      { pagina: filtros.pagina, basica: filtros.basica, momento_id: filtros.momento ?? undefined, santo_id: filtros.santo ?? undefined }, { signal }),
    { verificarSeVazio: paginaEstaVazia },
  );
  if (resultado.estado === "cancelado") return;
  areaDasOracoes.setAttribute("aria-busy", "false");

  if (resultado.estado === "erro") {
    areaDasOracoes.innerHTML = mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "as orações" });
    ligarTentarNovamente(areaDasOracoes, carregarOracoes);
  } else if (resultado.estado === "vazio") {
    textoDaContagem = "Nenhuma oração";
    areaDasOracoes.innerHTML = mensagemDeListaVazia({
      titulo: "Nenhuma oração com esses filtros", texto: "Experimente outro momento do dia ou outro santo.",
      acao: filtros.temFiltroAtivo ? botao({ variante: "secundario", icone: "fechar", texto: "Limpar filtros", atributos: "data-limpar-filtros" }) : null,
    });
    areaDasOracoes.querySelector("[data-limpar-filtros]")?.addEventListener("click", limparFiltros);
  } else {
    const paginaDeOracoes = resultado.dados;
    const totalDeOracoes = paginaDeOracoes.total_registros_filtros;
    textoDaContagem = `${totalDeOracoes} ${totalDeOracoes === 1 ? "oração" : "orações"}`;
    areaDasOracoes.innerHTML = `<div class="grade-de-oracoes">${paginaDeOracoes.itens.map((oracao) => cardDaOracao(oracao, 2)).join("")}</div>`
      + paginacao({ pagina: paginaDeOracoes.pagina, totalPaginas: paginaDeOracoes.total_paginas, totalRegistros: totalDeOracoes, rotulo: "Páginas de orações" });
    ligarCardsDeOracao(areaDasOracoes);
    ligarPaginacao(areaDasOracoes, irParaPagina);
  }
  desenharFiltros();
}

// redesenha tudo que depende dos filtros
function atualizarTela() {
  desenharDestaque();
  carregarOracoes();
}

aoMudarParametrosDaUrl(atualizarTela);
desenharDestaque();
carregarMomentos();
carregarSantosDoFiltro();
carregarOracoes();

// Livros: recomendações no topo (com base nos santos visitados neste aparelho)
// e o catálogo completo com filtro por santo e paginação.
import { montarLayout } from "../layout.js";
import { servicoLivros, servicoSantos, listarTodasAsPaginas } from "../api/servicos.js";
import { criarConsulta, paginaEstaVazia } from "../utils/consulta.js";
import { lerParametrosDaUrl, atualizarParametrosDaUrl, aoMudarParametrosDaUrl } from "../utils/url.js";
import { lerIdDaUrl, lerNumeroDaPagina } from "../utils/paginacao.js";
import { enderecos } from "../utils/enderecos.js";
import { listarSantosAcessados } from "../estado/santosAcessados.js";
import { escaparHtml } from "../componentes/html.js";
import { icone } from "../componentes/icones.js";
import {
  botao, botaoLink, card, carregando, mensagemDeErro, mensagemDeListaVazia, ligarPaginacao, ligarTentarNovamente, paginacao, seletor,
} from "../componentes/componentes.js";

montarLayout();

const areaDasRecomendacoes = document.getElementById("livros-recomendados");
const areaDoFiltro = document.getElementById("filtro-por-santo");
const areaDoCatalogo = document.getElementById("catalogo-de-livros");
const consultarLivros = criarConsulta();
let opcoesDeSanto = null;

// "Autor · Santo" (o santo só aparece se for diferente do autor)
const escreverAutoriaDoLivro = (livro) =>
  [livro.autor, livro.santo?.nome && livro.santo.nome !== livro.autor ? livro.santo.nome : null].filter(Boolean).join(" · ");

// recomendação de leitura: livros dos santos visitados (GET /livros/recomendados?santo_id=...)
async function carregarRecomendacoes() {
  const idsDosSantosAcessados = listarSantosAcessados();
  if (idsDosSantosAcessados.length === 0) {
    areaDasRecomendacoes.innerHTML = card({
      simples: true, nivel: 3, titulo: "Ainda sem recomendações",
      corpo: '<p class="texto-do-card">Visite a página de um santo e os livros ligados a ele aparecerão aqui.</p>'
        + `<div class="botoes-do-card">${botaoLink({ variante: "secundario", icone: "santos", para: enderecos.santos(), texto: "Explorar santos" })}</div>`,
    });
    return;
  }
  areaDasRecomendacoes.innerHTML = carregando({ quantidade: 2, texto: "Carregando recomendações…" });
  const resultado = await criarConsulta()(
    (signal) => servicoLivros.listarLivrosRecomendados(idsDosSantosAcessados, {}, { signal }),
    { verificarSeVazio: paginaEstaVazia },
  );
  if (resultado.estado === "erro") {
    areaDasRecomendacoes.innerHTML = mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "as recomendações" });
    ligarTentarNovamente(areaDasRecomendacoes, carregarRecomendacoes);
  } else if (resultado.estado === "vazio") {
    areaDasRecomendacoes.innerHTML = '<p class="texto-auxiliar">Os santos que você visitou ainda não têm livros cadastrados. Veja o catálogo abaixo.</p>';
  } else {
    areaDasRecomendacoes.innerHTML = `<div class="grade grade-de-3-colunas">${resultado.dados.itens.map((livro) =>
      card({ titulo: livro.titulo, para: enderecos.livro(livro.id), meta: escreverAutoriaDoLivro(livro), rotulo: "Recomendação de leitura" })).join("")}</div>`;
  }
}

function filtrarPorSanto(santoId) {
  const novosParametros = new URLSearchParams();
  if (santoId) novosParametros.set("santo", santoId);
  atualizarParametrosDaUrl(novosParametros, { substituir: true });
  desenharFiltro();
  carregarCatalogo();
}

function irParaPagina(numeroDaPagina) {
  const parametrosDaUrl = lerParametrosDaUrl();
  parametrosDaUrl.set("pagina", String(numeroDaPagina));
  atualizarParametrosDaUrl(parametrosDaUrl);
  carregarCatalogo();
}

function desenharFiltro() {
  const santoFiltrado = lerIdDaUrl(lerParametrosDaUrl().get("santo"));
  areaDoFiltro.innerHTML = seletor({
    rotulo: "Filtrar por santo", valor: santoFiltrado ?? "", textoDeTodos: "Todos os livros",
    desabilitado: opcoesDeSanto === null, opcoes: opcoesDeSanto ?? [],
  });
  areaDoFiltro.querySelector("select").addEventListener("change", (evento) => filtrarPorSanto(evento.target.value));
}

async function carregarOpcoesDeSanto() {
  try {
    const santos = await listarTodasAsPaginas((filtros, opcoes) => servicoSantos.listarSantos(filtros, opcoes));
    opcoesDeSanto = santos.map((santo) => ({ valor: santo.id, rotulo: santo.nome }));
  } catch {
    opcoesDeSanto = null;
  }
  desenharFiltro();
}

async function carregarCatalogo() {
  const parametrosDaUrl = lerParametrosDaUrl();
  const santoFiltrado = lerIdDaUrl(parametrosDaUrl.get("santo"));
  const pagina = lerNumeroDaPagina(parametrosDaUrl.get("pagina"));
  areaDoCatalogo.innerHTML = carregando({ quantidade: 4, texto: "Carregando livros…" });
  const resultado = await consultarLivros(
    (signal) => servicoLivros.listarLivros({ pagina, santo_id: santoFiltrado ?? undefined }, { signal }),
    { verificarSeVazio: paginaEstaVazia },
  );
  if (resultado.estado === "cancelado") return;

  if (resultado.estado === "erro") {
    areaDoCatalogo.innerHTML = mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "os livros" });
    ligarTentarNovamente(areaDoCatalogo, carregarCatalogo);
  } else if (resultado.estado === "vazio") {
    areaDoCatalogo.innerHTML = mensagemDeListaVazia({
      titulo: "Nenhum livro encontrado",
      texto: santoFiltrado ? "Este santo ainda não tem livros cadastrados." : null,
      acao: santoFiltrado ? botao({ variante: "secundario", icone: "fechar", texto: "Ver todos os livros", atributos: "data-ver-todos" }) : null,
    });
    areaDoCatalogo.querySelector("[data-ver-todos]")?.addEventListener("click", () => filtrarPorSanto(""));
  } else {
    const paginaDeLivros = resultado.dados;
    const itensDaLista = paginaDeLivros.itens.map((livro) =>
      `<li><div><a class="titulo-do-item-da-lista" href="${enderecos.livro(livro.id)}">${escaparHtml(livro.titulo)}</a><p class="texto-auxiliar">${escaparHtml(escreverAutoriaDoLivro(livro))}</p></div>${icone("direita")}</li>`).join("");
    areaDoCatalogo.innerHTML = `<ul class="lista lista-de-links">${itensDaLista}</ul>`
      + paginacao({ pagina: paginaDeLivros.pagina, totalPaginas: paginaDeLivros.total_paginas, totalRegistros: paginaDeLivros.total_registros_filtros, rotulo: "Páginas de livros" });
    ligarPaginacao(areaDoCatalogo, irParaPagina);
  }
}

aoMudarParametrosDaUrl(() => { desenharFiltro(); carregarCatalogo(); });
desenharFiltro();
carregarRecomendacoes();
carregarOpcoesDeSanto();
carregarCatalogo();

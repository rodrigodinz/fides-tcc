// Catálogo de novenas com filtro por santo; cada card mostra a situação da agenda.
import { montarLayout } from "../layout.js";
import { servicoNovenas, servicoSantos, listarTodasAsPaginas } from "../api/servicos.js";
import { criarConsulta, paginaEstaVazia } from "../utils/consulta.js";
import { lerParametrosDaUrl, atualizarParametrosDaUrl, aoMudarParametrosDaUrl } from "../utils/url.js";
import { lerIdDaUrl, lerNumeroDaPagina } from "../utils/paginacao.js";
import {
  botao, cardNovena, carregando, estadoErro, estadoVazio, ligarPaginacao, ligarTentarNovamente, paginacao, seletor,
} from "../componentes/componentes.js";

montarLayout();

const areaDoFiltro = document.getElementById("filtro-por-santo");
const areaDasNovenas = document.getElementById("lista-de-novenas");
const consultarNovenas = criarConsulta();
let opcoesDeSanto = null;  // enquanto for null, o filtro fica desabilitado

// o filtro guarda o santo na URL (?santo=2) e volta para a página 1
function filtrarPorSanto(santoId) {
  const novosParametros = new URLSearchParams();
  if (santoId) novosParametros.set("santo", santoId);
  atualizarParametrosDaUrl(novosParametros, { substituir: true });
  desenharFiltro();
  carregarNovenas();
}

function irParaPagina(numeroDaPagina) {
  const parametrosDaUrl = lerParametrosDaUrl();
  parametrosDaUrl.set("pagina", String(numeroDaPagina));
  atualizarParametrosDaUrl(parametrosDaUrl);
  carregarNovenas();
}

function desenharFiltro() {
  const santoFiltrado = lerIdDaUrl(lerParametrosDaUrl().get("santo"));
  areaDoFiltro.innerHTML = seletor({
    rotulo: "Filtrar por santo", valor: santoFiltrado ?? "", textoDeTodos: "Todos os santos",
    desabilitado: opcoesDeSanto === null, opcoes: opcoesDeSanto ?? [],
  });
  areaDoFiltro.querySelector("select").addEventListener("change", (evento) => filtrarPorSanto(evento.target.value));
}

// a lista de santos do filtro vem de todas as páginas de GET /santos
async function carregarOpcoesDeSanto() {
  try {
    const santos = await listarTodasAsPaginas((filtros, opcoes) => servicoSantos.listarSantos(filtros, opcoes));
    opcoesDeSanto = santos.map((santo) => ({ valor: santo.id, rotulo: santo.nome }));
  } catch {
    opcoesDeSanto = null;
  }
  desenharFiltro();
}

async function carregarNovenas() {
  const parametrosDaUrl = lerParametrosDaUrl();
  const santoFiltrado = lerIdDaUrl(parametrosDaUrl.get("santo"));
  const pagina = lerNumeroDaPagina(parametrosDaUrl.get("pagina"));
  areaDasNovenas.setAttribute("aria-busy", "true");
  areaDasNovenas.innerHTML = carregando({ quantidade: 4, texto: "Carregando novenas…" });
  const resultado = await consultarNovenas(
    (signal) => servicoNovenas.listarNovenas({ pagina, santo_id: santoFiltrado ?? undefined }, { signal }),
    { verificarSeVazio: paginaEstaVazia },
  );
  if (resultado.estado === "cancelado") return;
  areaDasNovenas.setAttribute("aria-busy", "false");

  if (resultado.estado === "erro") {
    areaDasNovenas.innerHTML = estadoErro({ erro: resultado.erro, conteudoBuscado: "as novenas" });
    ligarTentarNovamente(areaDasNovenas, carregarNovenas);
  } else if (resultado.estado === "vazio") {
    areaDasNovenas.innerHTML = estadoVazio({
      titulo: "Nenhuma novena encontrada",
      texto: santoFiltrado ? "Este santo ainda não tem novenas cadastradas." : null,
      acao: santoFiltrado ? botao({ variante: "secundario", icone: "fechar", texto: "Ver todas as novenas", atributos: "data-ver-todas" }) : null,
    });
    areaDasNovenas.querySelector("[data-ver-todas]")?.addEventListener("click", () => filtrarPorSanto(""));
  } else {
    const paginaDeNovenas = resultado.dados;
    areaDasNovenas.innerHTML = `<div class="fd-grade fd-grade--2">${paginaDeNovenas.itens.map((novena) => cardNovena(novena)).join("")}</div>`
      + paginacao({ pagina: paginaDeNovenas.pagina, totalPaginas: paginaDeNovenas.total_paginas, totalRegistros: paginaDeNovenas.total_registros_filtros, rotulo: "Páginas de novenas" });
    ligarPaginacao(areaDasNovenas, irParaPagina);
  }
}

aoMudarParametrosDaUrl(() => { desenharFiltro(); carregarNovenas(); });
desenharFiltro();
carregarOpcoesDeSanto();
carregarNovenas();

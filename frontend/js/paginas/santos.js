// Lista e busca de santos. O texto buscado fica na URL (?nome=), então voltar no navegador
// mantém a busca. A busca só dispara 350 ms depois que a pessoa para de digitar.
import { montarLayout } from "../layout.js";
import { servicoSantos } from "../api/servicos.js";
import { criarConsulta, paginaEstaVazia } from "../utils/consulta.js";
import { lerParametrosDaUrl, atualizarParametrosDaUrl, aoMudarParametrosDaUrl } from "../utils/url.js";
import { lerNumeroDaPagina } from "../utils/paginacao.js";
import { escaparHtml } from "../componentes/html.js";
import {
  botao, cardSanto, carregando, estadoErro, estadoVazio, ligarPaginacao, ligarTentarNovamente, paginacao,
} from "../componentes/componentes.js";

montarLayout();

const campoDeBusca = document.getElementById("busca-santo");
const botaoLimparBusca = document.querySelector("[data-limpar-busca]");
const areaDosResultados = document.getElementById("resultados");
const consultarSantos = criarConsulta();
const Tempo_De_Espera_Da_Busca = 350;
let temporizadorDaBusca = null;

// o botão "x" dentro do campo só aparece quando há texto digitado
function atualizarBotaoLimpar() {
  botaoLimparBusca.hidden = campoDeBusca.value === "";
}

// espera a pessoa parar de digitar e só então grava o texto na URL e busca de novo
function aoDigitar() {
  atualizarBotaoLimpar();
  clearTimeout(temporizadorDaBusca);
  temporizadorDaBusca = setTimeout(() => {
    const parametrosDaUrl = lerParametrosDaUrl();
    const nomeDigitado = campoDeBusca.value.trim();
    if (nomeDigitado === (parametrosDaUrl.get("nome") ?? "").trim()) return;
    if (nomeDigitado) parametrosDaUrl.set("nome", nomeDigitado); else parametrosDaUrl.delete("nome");
    parametrosDaUrl.delete("pagina");  // busca nova sempre volta para a página 1
    atualizarParametrosDaUrl(parametrosDaUrl, { substituir: true });
    carregarSantos();
  }, Tempo_De_Espera_Da_Busca);
}

function limparBusca() {
  campoDeBusca.value = "";
  aoDigitar();
  campoDeBusca.focus();
}

function irParaPagina(numeroDaPagina) {
  const parametrosDaUrl = lerParametrosDaUrl();
  parametrosDaUrl.set("pagina", String(numeroDaPagina));
  atualizarParametrosDaUrl(parametrosDaUrl);
  carregarSantos();
}

async function carregarSantos() {
  const parametrosDaUrl = lerParametrosDaUrl();
  const nomeBuscado = parametrosDaUrl.get("nome") ?? "";
  const pagina = lerNumeroDaPagina(parametrosDaUrl.get("pagina"));

  // primeiro mostra os esqueletos; depois troca pelo resultado
  areaDosResultados.setAttribute("aria-busy", "true");
  areaDosResultados.innerHTML = carregando({ tipo: "santos", quantidade: 3, texto: "Carregando santos…" });
  const resultado = await consultarSantos(
    (signal) => servicoSantos.listarSantos({ nome: nomeBuscado, pagina }, { signal }),
    { verificarSeVazio: paginaEstaVazia },
  );
  if (resultado.estado === "cancelado") return;  // a pessoa já pediu outra busca: ignora esta
  areaDosResultados.setAttribute("aria-busy", "false");

  if (resultado.estado === "erro") {
    areaDosResultados.innerHTML = estadoErro({ erro: resultado.erro, conteudoBuscado: "os santos" });
    ligarTentarNovamente(areaDosResultados, carregarSantos);
  } else if (resultado.estado === "vazio") {
    areaDosResultados.innerHTML = estadoVazio({
      titulo: nomeBuscado ? `Nenhum santo encontrado para “${nomeBuscado}”` : "Nenhum santo cadastrado",
      texto: nomeBuscado ? "Confira a grafia ou veja todos os santos." : null,
      acao: nomeBuscado ? botao({ variante: "secundario", icone: "fechar", texto: "Limpar busca", atributos: "data-limpar-resultado" }) : null,
    });
    areaDosResultados.querySelector("[data-limpar-resultado]")?.addEventListener("click", limparBusca);
  } else {
    const paginaDeSantos = resultado.dados;
    const totalDeSantos = paginaDeSantos.total_registros_filtros;
    areaDosResultados.innerHTML =
      `<p class="fd-aux" role="status" style="margin-bottom:16px">${totalDeSantos} ${totalDeSantos === 1 ? "santo" : "santos"}${nomeBuscado ? ` para “${escaparHtml(nomeBuscado)}”` : ""}</p>`
      + `<div class="fd-grade fd-grade--3">${paginaDeSantos.itens.map((santo) => cardSanto(santo, 2)).join("")}</div>`
      + paginacao({ pagina: paginaDeSantos.pagina, totalPaginas: paginaDeSantos.total_paginas, totalRegistros: totalDeSantos, rotulo: "Páginas de santos" });
    ligarPaginacao(areaDosResultados, irParaPagina);
  }
}

// quando a página abre, o campo mostra o que já estava na URL
campoDeBusca.value = lerParametrosDaUrl().get("nome") ?? "";
atualizarBotaoLimpar();
campoDeBusca.addEventListener("input", aoDigitar);
botaoLimparBusca.addEventListener("click", limparBusca);
aoMudarParametrosDaUrl(() => {
  campoDeBusca.value = lerParametrosDaUrl().get("nome") ?? "";
  atualizarBotaoLimpar();
  carregarSantos();
});
carregarSantos();

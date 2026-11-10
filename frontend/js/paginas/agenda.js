// Agenda do dia: novenas em andamento e liturgia de uma data (GET /agenda?data=...).
import { montarLayout } from "../layout.js";
import { servicoAgenda } from "../api/servicos.js";
import { ErroDaApi } from "../api/cliente.js";
import { criarConsulta } from "../utils/consulta.js";
import { aoMudarParametrosDaUrl } from "../utils/url.js";
import { lerDataDaUrl, definirDataNaUrl } from "../utils/dataNaUrl.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { ordenarHorasDaLiturgia } from "../utils/liturgia.js";
import { enderecos } from "../utils/enderecos.js";
import { escaparHtml } from "../componentes/html.js";
import { icone } from "../componentes/icones.js";
import {
  avisoDemonstracao, botaoLink, cabecalhoDaPagina, card, carregando, erroDeData, ligarSeletorDeData, seletorDeData, tituloDeSecao,
} from "../componentes/componentes.js";

montarLayout();

const topoDaPagina = document.getElementById("topo-da-pagina");
const conteudoDaAgenda = document.getElementById("conteudo-da-agenda");
const consultarAgenda = criarConsulta();
let periodoConhecido = null;

function desenharTopo({ data, conteudosDoDia }) {
  const dataExibida = conteudosDoDia?.data ?? data ?? periodoConhecido?.hoje;
  topoDaPagina.innerHTML = cabecalhoDaPagina({
    titulo: "Agenda do dia", rotulo: dataExibida ? escreverDataPorExtenso(dataExibida) : "Agenda",
    textoDeAbertura: "A liturgia e as novenas em andamento na data escolhida.",
  }) + (periodoConhecido && dataExibida ? seletorDeData({ data: dataExibida, periodo: periodoConhecido }) : "");
  ligarSeletorDeData(topoDaPagina, (dataEscolhida) => mudarData(dataEscolhida));
}

function mudarData(dataEscolhida) {
  definirDataNaUrl(dataEscolhida, periodoConhecido ?? {});
  carregarAgenda();
}

function desenharAgenda(conteudosDoDia) {
  const parametroDaData = conteudosDoDia.data;
  const novenasDoDia = conteudosDoDia.novenas_em_andamento.length === 0
    ? `<p class="texto-auxiliar">Nenhuma novena em andamento nesta data. <a class="link" href="${enderecos.novenas()}">Ver todas as novenas</a></p>`
    : `<div class="grade grade-de-2-colunas">${conteudosDoDia.novenas_em_andamento.map((novenaEmAndamento) => card({
      destaque: true, titulo: novenaEmAndamento.novena.titulo, para: enderecos.novena(novenaEmAndamento.novena.id),
      rotulo: `Dia ${novenaEmAndamento.dia_atual} de ${novenaEmAndamento.total_dias}`, meta: novenaEmAndamento.novena.santo?.nome,
      acoes: botaoLink({ variante: "especial", texto: `Ler o dia ${novenaEmAndamento.dia_atual}`, para: enderecos.novena(novenaEmAndamento.novena.id, novenaEmAndamento.dia_atual) }),
    })).join("")}</div>`;

  const liturgiaDoDia = conteudosDoDia.liturgia_do_dia;
  const cardDaLiturgiaDoDia = card({
    titulo: "Liturgia do Dia", para: enderecos.liturgiaDoDia(parametroDaData), meta: liturgiaDoDia?.santo_celebrado ?? null,
    corpo: liturgiaDoDia
      ? `<ul class="lista" style="margin-top:12px"><li>Primeira Leitura</li><li>Salmo Responsorial</li>${liturgiaDoDia.segunda_leitura ? "<li>Segunda Leitura</li>" : ""}<li>Evangelho</li></ul>`
      : '<p class="texto-do-card">Não há Liturgia do Dia cadastrada para esta data.</p>',
  });
  const cardDaLiturgiaDasHoras = card({
    titulo: "Liturgia das Horas", para: enderecos.liturgiaDasHoras(parametroDaData),
    corpo: conteudosDoDia.liturgia_das_horas.length > 0
      ? `<ul class="lista" style="margin-top:12px">${ordenarHorasDaLiturgia(conteudosDoDia.liturgia_das_horas).map((hora) =>
        `<li>${icone("horas", { classe: "icone-no-meio-do-texto" })} ${escaparHtml(hora.bloco.nome)}</li>`).join("")}</ul>`
      : '<p class="texto-do-card">Não há Liturgia das Horas cadastrada para esta data.</p>',
  });

  conteudoDaAgenda.innerHTML =
    `<section class="secao" aria-labelledby="titulo-das-novenas-de-hoje">${tituloDeSecao({ id: "titulo-das-novenas-de-hoje", titulo: "Novenas em andamento" })}${novenasDoDia}</section>`
    + `<section class="secao" aria-labelledby="titulo-da-liturgia-de-hoje">${tituloDeSecao({ id: "titulo-da-liturgia-de-hoje", titulo: "Liturgia" })}${avisoDemonstracao(conteudosDoDia.aviso)}`
    + `<div class="grade grade-de-2-colunas" style="margin-top:24px">${cardDaLiturgiaDoDia}${cardDaLiturgiaDasHoras}</div></section>`;
}

async function carregarAgenda() {
  const { data, dataInvalida } = lerDataDaUrl();
  desenharTopo({ data });
  conteudoDaAgenda.innerHTML = `<div class="secao">${carregando({ quantidade: 3, texto: "Carregando a agenda…" })}</div>`;
  const resultado = await consultarAgenda((signal) => {
    if (dataInvalida) return Promise.reject(new ErroDaApi({ codigo: "PARAMETRO_INVALIDO", mensagem: "Data inválida." }));
    return servicoAgenda.verConteudosDoDia(data, { signal });
  });
  if (resultado.estado === "cancelado") return;

  if (resultado.estado === "erro") {
    conteudoDaAgenda.innerHTML = `<div class="secao largura-de-leitura" style="margin-inline:auto">${erroDeData(resultado.erro)}</div>`;
    conteudoDaAgenda.querySelector('[data-acao="ir-para-hoje"]')?.addEventListener("click", () => mudarData(undefined));
    conteudoDaAgenda.querySelector('[data-acao="tentar-novamente"]')?.addEventListener("click", carregarAgenda);
    return;
  }
  periodoConhecido = resultado.dados.periodo;
  desenharTopo({ data, conteudosDoDia: resultado.dados });
  desenharAgenda(resultado.dados);
}

aoMudarParametrosDaUrl(carregarAgenda);
carregarAgenda();

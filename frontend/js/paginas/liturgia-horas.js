// Liturgia das Horas: Laudes, Horas médias e Vésperas da data escolhida.
import { montarLayout } from "../layout.js";
import { servicoLiturgia } from "../api/servicos.js";
import { ErroDaApi } from "../api/cliente.js";
import { criarConsulta } from "../utils/consulta.js";
import { aoMudarParametrosDaUrl } from "../utils/url.js";
import { lerDataDaUrl, definirDataNaUrl } from "../utils/dataNaUrl.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { ordenarHorasDaLiturgia } from "../utils/liturgia.js";
import { escaparHtml } from "../componentes/html.js";
import {
  abasDaLiturgia, avisoDemonstracao, cabecalhoDaPagina, carregando, erroDeData, mensagemDeListaVazia, ligarSeletorDeData, ornamento, seletorDeData,
} from "../componentes/componentes.js";

montarLayout();

const topoDaPagina = document.getElementById("topo-da-pagina");
const conteudoDasHoras = document.getElementById("conteudo-da-liturgia");
const consultarHoras = criarConsulta();
let periodoConhecido = null;

function desenharTopo({ data, liturgiaDasHoras }) {
  const dataExibida = liturgiaDasHoras?.data ?? data ?? periodoConhecido?.hoje;
  topoDaPagina.innerHTML = cabecalhoDaPagina({
    titulo: "Liturgia das Horas", rotulo: dataExibida ? escreverDataPorExtenso(dataExibida) : "Liturgia",
    textoDeAbertura: "Laudes, Horas médias e Vésperas.",
  })
    + abasDaLiturgia(data)
    + (periodoConhecido && dataExibida ? seletorDeData({ data: dataExibida, periodo: periodoConhecido }) : "");
  ligarSeletorDeData(topoDaPagina, (dataEscolhida) => mudarData(dataEscolhida));
}

function mudarData(dataEscolhida) {
  definirDataNaUrl(dataEscolhida, periodoConhecido ?? {});
  carregarHoras();
}

async function carregarHoras() {
  const { data, dataInvalida } = lerDataDaUrl();
  desenharTopo({ data });
  conteudoDasHoras.innerHTML = carregando({ tipo: "texto", quantidade: 6, texto: "Carregando a Liturgia das Horas…" });
  const resultado = await consultarHoras((signal) => {
    if (dataInvalida) return Promise.reject(new ErroDaApi({ codigo: "PARAMETRO_INVALIDO", mensagem: "Data inválida." }));
    return servicoLiturgia.verLiturgiaDasHoras(data, undefined, { signal });
  }, { verificarSeVazio: (liturgia) => liturgia.horas.length === 0 });
  if (resultado.estado === "cancelado") return;

  if (resultado.estado === "erro") {
    conteudoDasHoras.innerHTML = erroDeData(resultado.erro);
    conteudoDasHoras.querySelector('[data-acao="ir-para-hoje"]')?.addEventListener("click", () => mudarData(undefined));
    conteudoDasHoras.querySelector('[data-acao="tentar-novamente"]')?.addEventListener("click", carregarHoras);
    return;
  }
  const liturgiaDasHoras = resultado.dados;
  periodoConhecido = liturgiaDasHoras.periodo;
  desenharTopo({ data, liturgiaDasHoras });
  if (resultado.estado === "vazio") {
    conteudoDasHoras.innerHTML = avisoDemonstracao(liturgiaDasHoras.aviso)
      + mensagemDeListaVazia({ titulo: "Sem Liturgia das Horas para esta data", texto: "Escolha outra data no período disponível." });
    return;
  }
  // um bloco por hora, sempre na ordem Laudes -> Horas médias -> Vésperas
  conteudoDasHoras.innerHTML = avisoDemonstracao(liturgiaDasHoras.aviso)
    + ordenarHorasDaLiturgia(liturgiaDasHoras.horas).map((hora) =>
      `<section class="bloco-de-leitura" aria-labelledby="h-${hora.bloco.codigo}">${ornamento("curto")}<h2 id="h-${hora.bloco.codigo}" class="subtitulo">${escaparHtml(hora.bloco.nome)}</h2><p class="texto-com-quebras-de-linha">${escaparHtml(hora.texto)}</p></section>`).join("");
}

aoMudarParametrosDaUrl(carregarHoras);
carregarHoras();

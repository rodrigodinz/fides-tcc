// Liturgia do Dia (Primeira leitura, Salmo e Evanelho)
// A Segunda Leitura só aparece em domingos e solenidades
import { montarLayout } from "../layout.js";
import { servicoLiturgia } from "../api/servicos.js";
import { ErroDaApi } from "../api/cliente.js";
import { criarConsulta } from "../utils/consulta.js";
import { aoMudarParametrosDaUrl } from "../utils/url.js";
import { lerDataDaUrl, definirDataNaUrl } from "../utils/dataNaUrl.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { escaparHtml } from "../componentes/html.js";
import {
  abasDaLiturgia, avisoDemonstracao, cabecalhoDaPagina, carregando, erroDeData, ligarSeletorDeData, ornamento, seletorDeData,
} from "../componentes/componentes.js";

montarLayout();

const topoDaPagina = document.getElementById("topo-da-pagina");
const conteudoDaLiturgia = document.getElementById("conteudo-da-liturgia");
const consultarLiturgia = criarConsulta();
let periodoConhecido = null;  // período (hoje ± 7) da última resposta (Mantém o negócio de data ativado na tela)

function desenharTopo({ data, liturgiaDoDia }) {
  const dataExibida = liturgiaDoDia?.data ?? data ?? periodoConhecido?.hoje;
  topoDaPagina.innerHTML = cabecalhoDaPagina({
    titulo: "Liturgia do Dia", rotulo: dataExibida ? escreverDataPorExtenso(dataExibida) : "Liturgia",
    textoDeAbertura: liturgiaDoDia?.santo_celebrado || null,
  })
    + abasDaLiturgia(data)
    + (periodoConhecido && dataExibida ? seletorDeData({ data: dataExibida, periodo: periodoConhecido }) : "");
  ligarSeletorDeData(topoDaPagina, (dataEscolhida) => mudarData(dataEscolhida));
}

function mudarData(dataEscolhida) {
  definirDataNaUrl(dataEscolhida, periodoConhecido ?? {});
  carregarLiturgia();
}

// cada leitura vira um bloco com rococó e título
const blocoDeLeitura = (rotulo, texto, ehCitacao) =>
  `<section class="bloco-de-leitura">${ornamento("curto")}<h2 class="subtitulo">${rotulo}</h2><p class="texto-com-quebras-de-linha${ehCitacao ? " citacao" : ""}">${escaparHtml(texto)}</p></section>`;

async function carregarLiturgia() {
  const { data, dataInvalida } = lerDataDaUrl();
  desenharTopo({ data });
  conteudoDaLiturgia.innerHTML = carregando({ tipo: "texto", quantidade: 6, texto: "Carregando a liturgia…" });
  const resultado = await consultarLiturgia((signal) => {
    // data digitada errada na URL nem chega a chamar a API
    if (dataInvalida) return Promise.reject(new ErroDaApi({ codigo: "PARAMETRO_INVALIDO", mensagem: "Data inválida." }));
    return servicoLiturgia.verLiturgiaDoDia(data, { signal });
  });
  if (resultado.estado === "cancelado") return;

  if (resultado.estado === "erro") {
    conteudoDaLiturgia.innerHTML = erroDeData(resultado.erro);
    conteudoDaLiturgia.querySelector('[data-acao="ir-para-hoje"]')?.addEventListener("click", () => mudarData(undefined));
    conteudoDaLiturgia.querySelector('[data-acao="tentar-novamente"]')?.addEventListener("click", carregarLiturgia);
    return;
  }
  const liturgiaDoDia = resultado.dados;
  periodoConhecido = liturgiaDoDia.periodo;
  desenharTopo({ data, liturgiaDoDia });
  const semLeituras = !liturgiaDoDia.primeira_leitura && !liturgiaDoDia.salmo && !liturgiaDoDia.evangelho && !liturgiaDoDia.segunda_leitura;
  conteudoDaLiturgia.innerHTML = avisoDemonstracao(liturgiaDoDia.aviso)
    + (liturgiaDoDia.primeira_leitura ? blocoDeLeitura("Primeira Leitura", liturgiaDoDia.primeira_leitura) : "")
    + (liturgiaDoDia.salmo ? blocoDeLeitura("Salmo Responsorial", liturgiaDoDia.salmo, true) : "")
    + (liturgiaDoDia.segunda_leitura ? blocoDeLeitura("Segunda Leitura", liturgiaDoDia.segunda_leitura) : "")
    + (liturgiaDoDia.evangelho ? blocoDeLeitura("Evangelho", liturgiaDoDia.evangelho) : "")
    + (semLeituras ? '<p class="texto-auxiliar">As leituras desta data não foram cadastradas.</p>' : "");
}

aoMudarParametrosDaUrl(carregarLiturgia);
carregarLiturgia();

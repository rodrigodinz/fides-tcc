// Detalhe do santo: biografia, novenas, livros e orações.
// Ao abrir, o id é guardado em "santos acessados" para a recomendação de livros.
import { montarLayout, definirTitulo } from "../layout.js";
import { servicoSantos, servicoOracoes, servicoNovenas } from "../api/servicos.js";
import { ehErroDeNaoEncontrado } from "../api/erros.js";
import { criarConsulta } from "../utils/consulta.js";
import { lerParametrosDaUrl } from "../utils/url.js";
import { lerIdDaUrl } from "../utils/paginacao.js";
import { enderecos } from "../utils/enderecos.js";
import { registrarSantoAcessado } from "../estado/santosAcessados.js";
import { escaparHtml } from "../componentes/html.js";
import { icone } from "../componentes/icones.js";
import {
  cabecalhoDaPagina, cardDaNovena, cardDaOracao, carregando, mensagemDeErro, ligarCardsDeOracao, ligarTentarNovamente,
  caminhoDeNavegacao, mensagemDeNaoEncontrado, ornamento, retratoDoSanto, tituloDeSecao,
} from "../componentes/componentes.js";

montarLayout();

const paginaDoSanto = document.getElementById("pagina-do-santo");
// o id vem da URL: santo.html?id=5 -> 5 (texto inválido vira null)
const santoId = lerIdDaUrl(lerParametrosDaUrl().get("id"));
const consultarSanto = criarConsulta();

const voltarParaSantos = { para: enderecos.santos(), texto: "Voltar aos santos" };
const montarCaminhoDeNavegacao = (nomeDoSanto) => caminhoDeNavegacao([
  { texto: "Início", para: enderecos.inicio() }, { texto: "Santos", para: enderecos.santos() }, { texto: nomeDoSanto ?? "Santo" },
]);

// orações do santo vêm de GET /oracoes?santo_id=... (só busca se o santo tiver alguma)
async function carregarOracoesDoSanto(area, totalDeOracoes) {
  if (totalDeOracoes === 0) { area.innerHTML = '<p class="texto-auxiliar">Nenhuma oração vinculada a este santo.</p>'; return; }
  area.innerHTML = carregando({ quantidade: 1, texto: "Carregando orações…" });
  const resultado = await criarConsulta()((signal) => servicoOracoes.listarOracoes({ santo_id: santoId }, { signal }));
  if (resultado.estado === "erro") {
    area.innerHTML = mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "as orações deste santo" });
    ligarTentarNovamente(area, () => carregarOracoesDoSanto(area, totalDeOracoes));
    return;
  }
  area.innerHTML = `<div class="pilha-de-cards">${resultado.dados.itens.map((oracao) => cardDaOracao(oracao)).join("")}</div>`;
  ligarCardsDeOracao(area);
}

// novenas do santo vêm de GET /novenas?santo_id=... (já com a situação da agenda)
async function carregarNovenasDoSanto(area, totalDeNovenas) {
  if (totalDeNovenas === 0) { area.innerHTML = '<p class="texto-auxiliar">Nenhuma novena vinculada a este santo.</p>'; return; }
  area.innerHTML = carregando({ quantidade: 1, texto: "Carregando novenas…" });
  const resultado = await criarConsulta()((signal) => servicoNovenas.listarNovenas({ santo_id: santoId }, { signal }));
  if (resultado.estado === "erro") {
    area.innerHTML = mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "as novenas deste santo" });
    ligarTentarNovamente(area, () => carregarNovenasDoSanto(area, totalDeNovenas));
    return;
  }
  area.innerHTML = `<div class="pilha-de-cards">${resultado.dados.itens.map((novena) => cardDaNovena(novena, 3)).join("")}</div>`;
}

function desenharSanto(santo) {
  const listaDeLivros = santo.livros.length === 0
    ? '<p class="texto-auxiliar">Nenhum livro vinculado a este santo.</p>'
    : `<ul class="lista lista-de-links" aria-labelledby="titulo-dos-livros">${santo.livros.map((livro) =>
      `<li><div><a class="titulo-do-item-da-lista" href="${enderecos.livro(livro.id)}">${escaparHtml(livro.titulo)}</a><p class="texto-auxiliar">${escaparHtml(livro.autor)}</p></div>${icone("direita")}</li>`).join("")}</ul>`;
  const biografia = santo.biografia
    ? `<p class="texto-com-quebras-de-linha">${escaparHtml(santo.biografia)}</p>`
    : '<p class="texto-auxiliar">Biografia ainda não cadastrada.</p>';

  paginaDoSanto.innerHTML = montarCaminhoDeNavegacao(santo.nome)
    + `<div class="topo-da-pagina-do-santo"><div class="moldura-do-retrato">${retratoDoSanto({ fotoUrl: santo.foto_url, nome: santo.nome, carregamento: "eager" })}</div>`
    + `<div>${cabecalhoDaPagina({ titulo: santo.nome, rotulo: "Santos" })}<div class="largura-de-leitura biografia-do-santo">${biografia}</div></div></div>`
    + ornamento("divisor")
    + '<div class="secoes-da-pagina-do-santo"><div>'
    + `<section aria-labelledby="titulo-das-novenas">${tituloDeSecao({ id: "titulo-das-novenas", titulo: "Novenas" })}<div id="novenas-do-santo"></div></section>`
    + `<section class="secao" aria-labelledby="titulo-dos-livros">${tituloDeSecao({ id: "titulo-dos-livros", titulo: "Livros" })}${listaDeLivros}</section>`
    + "</div>"
    + `<section aria-labelledby="titulo-das-oracoes">${tituloDeSecao({ id: "titulo-das-oracoes", titulo: "Orações" })}<div id="oracoes-do-santo"></div></section>`
    + "</div>";

  // as duas listas carregam em paralelo, cada uma na sua área
  carregarNovenasDoSanto(document.getElementById("novenas-do-santo"), santo.novenas.length);
  carregarOracoesDoSanto(document.getElementById("oracoes-do-santo"), santo.oracoes.length);
}

async function carregarSanto() {
  if (santoId === null) {
    paginaDoSanto.innerHTML = mensagemDeNaoEncontrado({ titulo: "Santo não encontrado", voltar: voltarParaSantos });
    return;
  }
  paginaDoSanto.innerHTML = montarCaminhoDeNavegacao() + carregando({ tipo: "texto", quantidade: 5, texto: "Carregando o santo…" });
  const resultado = await consultarSanto((signal) => servicoSantos.detalharSanto(santoId, { signal }));
  if (resultado.estado === "cancelado") return;
  if (resultado.estado === "erro") {
    if (ehErroDeNaoEncontrado(resultado.erro)) {
      paginaDoSanto.innerHTML = mensagemDeNaoEncontrado({ titulo: "Santo não encontrado", voltar: voltarParaSantos });
      return;
    }
    paginaDoSanto.innerHTML = montarCaminhoDeNavegacao() + mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "este santo" });
    ligarTentarNovamente(paginaDoSanto, carregarSanto);
    return;
  }
  definirTitulo(resultado.dados.nome);
  registrarSantoAcessado(resultado.dados.id);  // guarda a visita no aparelho (recomendação de livros)
  desenharSanto(resultado.dados);
}

carregarSanto();

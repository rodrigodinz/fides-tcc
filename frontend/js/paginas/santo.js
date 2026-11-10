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
  cabecalhoPagina, cardNovena, cardOracao, carregando, estadoErro, ligarCardsDeOracao, ligarTentarNovamente,
  migalhas, naoEncontrado, ornamento, retratoSanto, tituloSecao,
} from "../componentes/componentes.js";

montarLayout();

const paginaDoSanto = document.getElementById("pagina-do-santo");
// o id vem da URL: santo.html?id=5 -> 5 (texto inválido vira null)
const santoId = lerIdDaUrl(lerParametrosDaUrl().get("id"));
const consultarSanto = criarConsulta();

const voltarParaSantos = { para: enderecos.santos(), texto: "Voltar aos santos" };
const montarMigalhas = (nomeDoSanto) => migalhas([
  { texto: "Início", para: enderecos.inicio() }, { texto: "Santos", para: enderecos.santos() }, { texto: nomeDoSanto ?? "Santo" },
]);

// orações do santo vêm de GET /oracoes?santo_id=... (só busca se o santo tiver alguma)
async function carregarOracoesDoSanto(area, totalDeOracoes) {
  if (totalDeOracoes === 0) { area.innerHTML = '<p class="fd-aux">Nenhuma oração vinculada a este santo.</p>'; return; }
  area.innerHTML = carregando({ quantidade: 1, texto: "Carregando orações…" });
  const resultado = await criarConsulta()((signal) => servicoOracoes.listarOracoes({ santo_id: santoId }, { signal }));
  if (resultado.estado === "erro") {
    area.innerHTML = estadoErro({ erro: resultado.erro, conteudoBuscado: "as orações deste santo" });
    ligarTentarNovamente(area, () => carregarOracoesDoSanto(area, totalDeOracoes));
    return;
  }
  area.innerHTML = `<div class="fd-pilha-cards">${resultado.dados.itens.map((oracao) => cardOracao(oracao)).join("")}</div>`;
  ligarCardsDeOracao(area);
}

// novenas do santo vêm de GET /novenas?santo_id=... (já com a situação da agenda)
async function carregarNovenasDoSanto(area, totalDeNovenas) {
  if (totalDeNovenas === 0) { area.innerHTML = '<p class="fd-aux">Nenhuma novena vinculada a este santo.</p>'; return; }
  area.innerHTML = carregando({ quantidade: 1, texto: "Carregando novenas…" });
  const resultado = await criarConsulta()((signal) => servicoNovenas.listarNovenas({ santo_id: santoId }, { signal }));
  if (resultado.estado === "erro") {
    area.innerHTML = estadoErro({ erro: resultado.erro, conteudoBuscado: "as novenas deste santo" });
    ligarTentarNovamente(area, () => carregarNovenasDoSanto(area, totalDeNovenas));
    return;
  }
  area.innerHTML = `<div class="fd-pilha-cards">${resultado.dados.itens.map((novena) => cardNovena(novena, 3)).join("")}</div>`;
}

function desenharSanto(santo) {
  const listaDeLivros = santo.livros.length === 0
    ? '<p class="fd-aux">Nenhum livro vinculado a este santo.</p>'
    : `<ul class="fd-lista fd-lista-rica" aria-labelledby="sec-livros">${santo.livros.map((livro) =>
      `<li><div><a class="fd-lista__titulo" href="${enderecos.livro(livro.id)}">${escaparHtml(livro.titulo)}</a><p class="fd-aux">${escaparHtml(livro.autor)}</p></div>${icone("direita")}</li>`).join("")}</ul>`;
  const biografia = santo.biografia
    ? `<p class="fd-texto-longo">${escaparHtml(santo.biografia)}</p>`
    : '<p class="fd-aux">Biografia ainda não cadastrada.</p>';

  paginaDoSanto.innerHTML = montarMigalhas(santo.nome)
    + `<div class="fd-santo-topo"><div class="fd-moldura">${retratoSanto({ fotoUrl: santo.foto_url, nome: santo.nome, carregamento: "eager" })}</div>`
    + `<div>${cabecalhoPagina({ titulo: santo.nome, rotulo: "Santos" })}<div class="fd-leitura fd-santo-bio">${biografia}</div></div></div>`
    + ornamento("divisor")
    + '<div class="fd-santo-secoes"><div>'
    + `<section aria-labelledby="sec-novenas">${tituloSecao({ id: "sec-novenas", titulo: "Novenas" })}<div id="novenas-do-santo"></div></section>`
    + `<section class="fd-secao" aria-labelledby="sec-livros">${tituloSecao({ id: "sec-livros", titulo: "Livros" })}${listaDeLivros}</section>`
    + "</div>"
    + `<section aria-labelledby="sec-oracoes">${tituloSecao({ id: "sec-oracoes", titulo: "Orações" })}<div id="oracoes-do-santo"></div></section>`
    + "</div>";

  // as duas listas carregam em paralelo, cada uma na sua área
  carregarNovenasDoSanto(document.getElementById("novenas-do-santo"), santo.novenas.length);
  carregarOracoesDoSanto(document.getElementById("oracoes-do-santo"), santo.oracoes.length);
}

async function carregarSanto() {
  if (santoId === null) {
    paginaDoSanto.innerHTML = naoEncontrado({ titulo: "Santo não encontrado", voltar: voltarParaSantos });
    return;
  }
  paginaDoSanto.innerHTML = montarMigalhas() + carregando({ tipo: "texto", quantidade: 5, texto: "Carregando o santo…" });
  const resultado = await consultarSanto((signal) => servicoSantos.detalharSanto(santoId, { signal }));
  if (resultado.estado === "cancelado") return;
  if (resultado.estado === "erro") {
    if (ehErroDeNaoEncontrado(resultado.erro)) {
      paginaDoSanto.innerHTML = naoEncontrado({ titulo: "Santo não encontrado", voltar: voltarParaSantos });
      return;
    }
    paginaDoSanto.innerHTML = montarMigalhas() + estadoErro({ erro: resultado.erro, conteudoBuscado: "este santo" });
    ligarTentarNovamente(paginaDoSanto, carregarSanto);
    return;
  }
  definirTitulo(resultado.dados.nome);
  registrarSantoAcessado(resultado.dados.id);  // guarda a visita no aparelho (recomendação de livros)
  desenharSanto(resultado.dados);
}

carregarSanto();

// Detalhe do livro: autor, santo, resumo e contexto histórico.
import { montarLayout, definirTitulo } from "../layout.js";
import { servicoLivros } from "../api/servicos.js";
import { ehErroDeNaoEncontrado } from "../api/erros.js";
import { criarConsulta } from "../utils/consulta.js";
import { lerParametrosDaUrl } from "../utils/url.js";
import { lerIdDaUrl } from "../utils/paginacao.js";
import { enderecos } from "../utils/enderecos.js";
import { escaparHtml } from "../componentes/html.js";
import {
  alerta, cabecalhoPagina, carregando, estadoErro, ligarTentarNovamente, migalhas, naoEncontrado, ornamento,
} from "../componentes/componentes.js";

montarLayout();

const paginaDoLivro = document.getElementById("pagina-do-livro");
const livroId = lerIdDaUrl(lerParametrosDaUrl().get("id"));
const consultarLivro = criarConsulta();
const voltarParaLivros = { para: enderecos.livros(), texto: "Voltar aos livros" };
const montarMigalhas = (tituloDoLivro) => migalhas([
  { texto: "Início", para: enderecos.inicio() }, { texto: "Livros", para: enderecos.livros() }, { texto: tituloDoLivro ?? "Livro" },
]);

// cada bloco (Resumo, Contexto histórico) só aparece se tiver texto
const blocoDeTexto = (id, titulo, texto) =>
  `<section class="fd-bloco" aria-labelledby="${id}">${ornamento("curto")}<h2 id="${id}" class="fd-h3">${titulo}</h2><p class="fd-texto-longo">${escaparHtml(texto)}</p></section>`;

function desenharLivro(livro) {
  const linkDoSanto = livro.santo
    ? `<p style="margin-top:6px;text-align:center"><a class="fd-link fd-link--vinho" href="${enderecos.santo(livro.santo.id)}">${escaparHtml(livro.santo.nome)}</a></p>`
    : "";
  const semTexto = !livro.resumo && !livro.contexto_historico
    ? alerta({ tipo: "info", titulo: "Sem resumo cadastrado", corpo: "O resumo e o contexto histórico deste livro ainda não foram cadastrados." })
    : "";
  paginaDoLivro.innerHTML = montarMigalhas(livro.titulo)
    + "<article>"
    + cabecalhoPagina({ titulo: livro.titulo, rotulo: "Livro", extra: `<p class="fd-livro-autor">${escaparHtml(livro.autor)}</p>${linkDoSanto}` })
    + ornamento("divisor")
    + '<div class="fd-blocos">'
    + (livro.resumo ? blocoDeTexto("resumo", "Resumo", livro.resumo) : "")
    + (livro.contexto_historico ? blocoDeTexto("contexto", "Contexto histórico", livro.contexto_historico) : "")
    + semTexto
    + "</div></article>";
}

async function carregarLivro() {
  if (livroId === null) {
    paginaDoLivro.innerHTML = naoEncontrado({ titulo: "Livro não encontrado", voltar: voltarParaLivros });
    return;
  }
  paginaDoLivro.innerHTML = montarMigalhas() + carregando({ tipo: "texto", quantidade: 5, texto: "Carregando o livro…" });
  const resultado = await consultarLivro((signal) => servicoLivros.detalharLivro(livroId, { signal }));
  if (resultado.estado === "cancelado") return;
  if (resultado.estado === "erro") {
    if (ehErroDeNaoEncontrado(resultado.erro)) {
      paginaDoLivro.innerHTML = naoEncontrado({ titulo: "Livro não encontrado", voltar: voltarParaLivros });
      return;
    }
    paginaDoLivro.innerHTML = montarMigalhas() + estadoErro({ erro: resultado.erro, conteudoBuscado: "este livro" });
    ligarTentarNovamente(paginaDoLivro, carregarLivro);
    return;
  }
  definirTitulo(resultado.dados.titulo);
  desenharLivro(resultado.dados);
}

carregarLivro();

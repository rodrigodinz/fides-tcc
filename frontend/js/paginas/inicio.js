// Página inicial: apresentação e atalhos (fixos no index.html) e três seções que vêm da API:
// "Hoje" (agenda), "Santos" (3 primeiros) e "Para continuar a leitura" (recomendação).
import { montarLayout } from "../layout.js";
import { servicoAgenda, servicoLivros, servicoSantos } from "../api/servicos.js";
import { criarConsulta } from "../utils/consulta.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { enderecos } from "../utils/enderecos.js";
import { listarSantosAcessados } from "../estado/santosAcessados.js";
import { escaparHtml } from "../componentes/html.js";
import {
  alerta, botaoLink, card, cardDoSanto, carregando, mensagemDeErro, ligarTentarNovamente, tituloDeSecao,
} from "../componentes/componentes.js";

montarLayout();

// ---------------------------------------------------------------- seção "Hoje"
function desenharNovenasDeHoje(conteudosDoDia) {
  if (conteudosDoDia.novenas_em_andamento.length === 0) {
    return card({
      simples: true, titulo: "Nenhuma novena em andamento hoje", nivel: 3,
      corpo: '<p class="texto-do-card">As novenas agendadas aparecem aqui no período em que estão sendo rezadas.</p>'
        + `<p style="margin-top:12px"><a class="link" href="${enderecos.novenas()}">Ver todas as novenas</a></p>`,
    });
  }
  return `<div class="pilha-de-cards">${conteudosDoDia.novenas_em_andamento.map((novenaEmAndamento) => card({
    destaque: true, nivel: 3,
    rotulo: `Em andamento · Dia ${novenaEmAndamento.dia_atual} de ${novenaEmAndamento.total_dias}`,
    titulo: novenaEmAndamento.novena.titulo, para: enderecos.novena(novenaEmAndamento.novena.id), meta: novenaEmAndamento.novena.santo?.nome,
    acoes: botaoLink({ variante: "especial", texto: `Ler o dia ${novenaEmAndamento.dia_atual}`, para: enderecos.novena(novenaEmAndamento.novena.id, novenaEmAndamento.dia_atual) }),
  })).join("")}</div>`;
}

function desenharLiturgiaDeHoje(conteudosDoDia) {
  const liturgiaDoDia = conteudosDoDia.liturgia_do_dia;
  const leituras = liturgiaDoDia
    ? `<ul class="lista" style="margin-top:16px"><li>Primeira Leitura</li><li>Salmo Responsorial</li>${liturgiaDoDia.segunda_leitura ? "<li>Segunda Leitura</li>" : ""}<li>Evangelho</li></ul>`
    : '<p class="texto-do-card">Não há liturgia cadastrada para hoje.</p>';
  const horas = conteudosDoDia.liturgia_das_horas.length > 0
    ? `<p class="texto-do-card acima-do-link-do-card"><a class="link" href="${enderecos.liturgiaDasHoras(conteudosDoDia.data)}">Liturgia das Horas: ${escaparHtml(conteudosDoDia.liturgia_das_horas.map((hora) => hora.bloco.nome).join(", "))}</a></p>`
    : "";
  return card({
    nivel: 3, rotulo: "Liturgia do Dia", titulo: liturgiaDoDia?.santo_celebrado || "Liturgia do Dia",
    para: enderecos.liturgiaDoDia(conteudosDoDia.data), meta: escreverDataPorExtenso(conteudosDoDia.data),
    corpo: leituras + horas,
  });
}

async function carregarSecaoHoje() {
  const secao = document.getElementById("secao-hoje");
  const tituloDaSecao = (descricao) => tituloDeSecao({
    id: "titulo-hoje", titulo: "Hoje", descricao, acao: `<a class="link" href="${enderecos.agenda()}">Ver a agenda completa</a>`,
  });
  secao.innerHTML = tituloDaSecao(null) + carregando({ quantidade: 2, texto: "Carregando a agenda de hoje…" });
  const resultado = await criarConsulta()((signal) => servicoAgenda.verConteudosDoDia(undefined, { signal }));
  if (resultado.estado === "erro") {
    secao.innerHTML = tituloDaSecao(null) + mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "a agenda de hoje" });
    ligarTentarNovamente(secao, carregarSecaoHoje);
    return;
  }
  const conteudosDoDia = resultado.dados;
  secao.innerHTML = tituloDaSecao(escreverDataPorExtenso(conteudosDoDia.data))
    + '<div class="conteudo-de-hoje">'
    + `<div><h3 class="subtitulo" style="margin-bottom:16px">Novenas em andamento</h3>${desenharNovenasDeHoje(conteudosDoDia)}</div>`
    + `<div><h3 class="subtitulo" style="margin-bottom:16px">Liturgia</h3>${desenharLiturgiaDeHoje(conteudosDoDia)}</div>`
    + "</div>"
    + `<div style="margin-top:24px">${alerta({ tipo: "aviso", titulo: "Liturgia de demonstração", papel: "note", corpo: `<p>${escaparHtml(conteudosDoDia.aviso)}</p>` })}</div>`;
}

// ---------------------------------------------------------------- seção "Santos"
async function carregarSecaoSantos() {
  const secao = document.getElementById("secao-santos");
  const tituloDaSecao = tituloDeSecao({
    id: "titulo-santos", titulo: "Santos", descricao: "Vidas, orações, novenas e livros de quem nos precede na fé.",
    acao: `<a class="link" href="${enderecos.santos()}">Ver todos os santos</a>`,
  });
  secao.innerHTML = tituloDaSecao + carregando({ tipo: "santos", quantidade: 3, texto: "Carregando santos…" });
  const resultado = await criarConsulta()((signal) => servicoSantos.listarSantos({ limite: 3 }, { signal }),
    { verificarSeVazio: (pagina) => pagina.itens.length === 0 });
  if (resultado.estado === "vazio") { secao.remove(); return; }  // sem santos cadastrados, a seção some
  if (resultado.estado === "erro") {
    secao.innerHTML = tituloDaSecao + mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "os santos" });
    ligarTentarNovamente(secao, carregarSecaoSantos);
    return;
  }
  secao.innerHTML = tituloDaSecao + `<div class="grade grade-de-3-colunas">${resultado.dados.itens.map((santo) => cardDoSanto(santo)).join("")}</div>`;
}

// ---------------------------------------------------------------- seção "Para continuar a leitura"
// só aparece se a pessoa já visitou algum santo neste aparelho e se houver livro recomendado
async function carregarSecaoRecomendados() {
  const secao = document.getElementById("secao-recomendados");
  const idsDosSantosAcessados = listarSantosAcessados();
  if (idsDosSantosAcessados.length === 0) { secao.remove(); return; }
  const tituloDaSecao = tituloDeSecao({
    id: "titulo-leituras", titulo: "Para continuar a leitura", descricao: "Livros dos santos que você visitou neste dispositivo.",
    acao: `<a class="link" href="${enderecos.livros()}">Ver livros</a>`,
  });
  secao.hidden = false;
  secao.innerHTML = tituloDaSecao + carregando({ quantidade: 2 });
  const resultado = await criarConsulta()(
    (signal) => servicoLivros.listarLivrosRecomendados(idsDosSantosAcessados, { limite: 3 }, { signal }),
    { verificarSeVazio: (pagina) => pagina.itens.length === 0 },
  );
  if (resultado.estado !== "sucesso") { secao.remove(); return; }
  secao.innerHTML = tituloDaSecao + `<div class="grade grade-de-3-colunas">${resultado.dados.itens.map((livro) => card({
    titulo: livro.titulo, para: enderecos.livro(livro.id), meta: [livro.autor, livro.santo?.nome].filter(Boolean).join(" · "), rotulo: "Recomendação de leitura",
  })).join("")}</div>`;
}

// as três seções carregam ao mesmo tempo, cada uma na sua área
carregarSecaoHoje();
carregarSecaoSantos();
carregarSecaoRecomendados();

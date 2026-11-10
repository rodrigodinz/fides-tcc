// Estrutura comum detodas as páginas (navbar, menu lateral, rodapé, avisos rápidos e janela de confirmação. 
// Cada página HTML chama montarLayout() logo no começo do seu script.
import { icone } from "./componentes/icones.js";
import { ornamento, retratoIndisponivel } from "./componentes/componentes.js";
import { criarElemento, escaparHtml } from "./componentes/html.js";

// Lista única dos módulos; a navbar, o menu lateral e o rodapé são montados a partir dela.
// "chave" identifica o módulo e cada página informa a sua chave.
export const Modulos = [
  { chave: "inicio", endereco: "/", nome: "Início", icone: "inicio" },
  { chave: "santos", endereco: "/santos.html", nome: "Santos", icone: "santos", aparecerNaNavbar: true },
  { chave: "oracoes", endereco: "/oracoes.html", nome: "Orações", icone: "oracoes", aparecerNaNavbar: true },
  { chave: "novenas", endereco: "/novenas.html", nome: "Novenas", icone: "novenas", aparecerNaNavbar: true },
  { chave: "livros", endereco: "/livros.html", nome: "Livros", icone: "livros" },
  { chave: "liturgia", endereco: "/liturgia.html", nome: "Liturgia do Dia", icone: "liturgia" },
  { chave: "liturgia-horas", endereco: "/liturgia-horas.html", nome: "Liturgia das Horas", icone: "horas" },
  { chave: "agenda", endereco: "/agenda.html", nome: "Agenda do dia", icone: "hoje" },
];

// aria-current="page" marca o link da página atual (o CSS usa isso para melhorar o link)
const marcarLinkDaPaginaAtual = (modulo, moduloAtual) => (modulo.chave === moduloAtual ? ' aria-current="page"' : "");

function montarNavbar(moduloAtual) {
  const linksDaNavbar = Modulos.filter((modulo) => modulo.aparecerNaNavbar).map((modulo) =>
    `<li><a class="link-da-navbar"${modulo.chave === moduloAtual ? ' aria-current="page"' : ""} href="${modulo.endereco}">${modulo.nome}</a></li>`).join("");
  return `<header class="navbar"><div class="conteudo-da-navbar">`
    + `<a class="simbolo-da-navbar" aria-label="Fides — página inicial" href="/"><img src="/imagens/simbolo-fides.svg" alt="" width="34" height="46"></a>`
    + `<a class="nome-fides-na-navbar" aria-hidden="true" tabindex="-1" href="/">FIDES</a>`
    + `<div class="lado-direito-da-navbar"><nav aria-label="Principal"><ul class="links-da-navbar">${linksDaNavbar}</ul></nav>`
    + `<button type="button" class="botao-de-icone" aria-label="Abrir menu" aria-expanded="false" aria-controls="menu-lateral">${icone("menu")}</button>`
    + "</div></div></header>";
}

function montarMenuLateral(moduloAtual) {
  const linksDoMenu = Modulos.map((modulo) =>
    `<li><a${marcarLinkDaPaginaAtual(modulo, moduloAtual)} href="${modulo.endereco}">${icone(modulo.icone, { tamanho: 24 })}${modulo.nome}</a></li>`).join("");
  return `<aside id="menu-lateral" class="menu-lateral" role="dialog" aria-modal="true" aria-label="Menu" aria-hidden="true">`
    + `<div class="topo-do-menu-lateral">${ornamento("curto")}<button type="button" class="botao-de-icone" aria-label="Fechar menu">${icone("fechar")}</button></div>`
    + `<nav class="links-do-menu-lateral" aria-label="Módulos"><ul>${linksDoMenu}</ul></nav>`
    + '<div class="sobre-o-fides-no-menu-lateral"><h2>Sobre o Fides</h2>'
    + "<p>Plataforma de conteúdo e práticas católicas: santos, orações, novenas, livros e liturgia reunidos em um só lugar.</p>"
    + "<p>Trabalho de Conclusão de Curso · versão MVP. A liturgia desta versão é conteúdo de demonstração.</p></div></aside>";
}

function montarRodape() {
  const linksDoRodape = Modulos.map((modulo) => `<li><a href="${modulo.endereco}">${modulo.nome}</a></li>`).join("");
  return '<footer class="rodape"><div class="faixa-azul-do-rodape"><div class="area-centralizada conteudo-da-faixa-azul-do-rodape">'
    + '<a class="marca-fides-no-rodape" href="/"><img src="/imagens/simbolo-fides.svg" alt="" width="30" height="40">FIDES</a>'
    + `<nav aria-label="Rodapé"><ul>${linksDoRodape}</ul></nav></div></div>`
    + '<div class="area-centralizada creditos-do-rodape"><span>Fides · Plataforma Integrada de Conteúdo e Práticas Católicas · Trabalho de Conclusão de Curso</span>'
    + "<span>Liturgia em conteúdo de demonstração: não é o texto oficial.</span></div></footer>";
}

const Seletor_De_Elementos_Focaveis = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

// com Tab, o foco gira só dentro do menu ou da janela de confirmação aberta
function prenderFocoNoContainer(eventoDeTeclado, container) {
  if (eventoDeTeclado.key !== "Tab" || !container) return;
  const elementosFocaveis = [...container.querySelectorAll(Seletor_De_Elementos_Focaveis)]
    .filter((elemento) => elemento.offsetParent !== null || elemento === document.activeElement);
  if (elementosFocaveis.length === 0) return;
  const primeiroElemento = elementosFocaveis[0];
  const ultimoElemento = elementosFocaveis[elementosFocaveis.length - 1];
  if (eventoDeTeclado.shiftKey && document.activeElement === primeiroElemento) {
    eventoDeTeclado.preventDefault();
    ultimoElemento.focus();
  } else if (!eventoDeTeclado.shiftKey && document.activeElement === ultimoElemento) {
    eventoDeTeclado.preventDefault();
    primeiroElemento.focus();
  }
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- menu lateral +-+-+-+-+-+-+-+-+-+-+-+-+-+-
function ligarMenuLateral(estadoDoLayout) {
  const botaoAbrir = document.querySelector('.navbar button[aria-controls="menu-lateral"]');
  const menu = document.getElementById("menu-lateral");
  const veuAtrasDoMenu = document.querySelector(".veu-atras-do-menu");
  const botaoFechar = menu.querySelector('button[aria-label="Fechar menu"]');

  const aoPressionarTecla = (evento) => {
    if (evento.key === "Escape") { evento.preventDefault(); fecharMenu(); }
    else prenderFocoNoContainer(evento, menu);
  };
  function abrirMenu() {
    estadoDoLayout.menuAberto = true;
    menu.classList.add("menu-lateral-quando-aberto");
    veuAtrasDoMenu.classList.add("veu-quando-aberto");
    menu.setAttribute("aria-hidden", "false");
    botaoAbrir.setAttribute("aria-expanded", "true");
    document.body.classList.add("pagina-sem-rolagem");  // trava a rolagem da página atrás do menu
    document.addEventListener("keydown", aoPressionarTecla);
    estadoDoLayout.mostrarNavbar();
    setTimeout(() => botaoFechar.focus(), 30);
  }
  function fecharMenu() {
    estadoDoLayout.menuAberto = false;
    menu.classList.remove("menu-lateral-quando-aberto");
    veuAtrasDoMenu.classList.remove("veu-quando-aberto");
    menu.setAttribute("aria-hidden", "true");
    botaoAbrir.setAttribute("aria-expanded", "false");
    document.body.classList.remove("pagina-sem-rolagem");
    document.removeEventListener("keydown", aoPressionarTecla);
    setTimeout(() => botaoAbrir.focus(), 0);  // devolve o foco ao botão que abriu o menu
  }
  botaoAbrir.addEventListener("click", abrirMenu);
  botaoFechar.addEventListener("click", fecharMenu);
  veuAtrasDoMenu.addEventListener("click", fecharMenu);
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- navbar que some quando rola pra baixo (lá ele) +-+-+-+-+-+-+-+-+-+-+-+-+-+-
export const Distancia_Minima_De_Rolagem = 24;
export const Altura_Da_Zona_Do_Topo = 16;

// esconde a navbar quando a pessoa rola para baixo e mostra de novo ao rolar para cima
function ligarNavbarQueSome(estadoDoLayout) {
  const navbar = document.querySelector(".navbar");
  let focoDentroDaNavbar = false;
  let ultimaPosicao = window.scrollY;
  let distanciaAcumulada = 0;
  let atualizacaoAgendada = false;
  const definirEscondida = (escondida) => navbar.classList.toggle("navbar-quando-escondida", escondida);
  estadoDoLayout.mostrarNavbar = () => { distanciaAcumulada = 0; definirEscondida(false); };

  navbar.addEventListener("focusin", () => { focoDentroDaNavbar = true; definirEscondida(false); });
  navbar.addEventListener("focusout", (evento) => { if (!navbar.contains(evento.relatedTarget)) focoDentroDaNavbar = false; });

  const atualizarNavbar = () => {
    atualizacaoAgendada = false;
    const posicaoAtual = window.scrollY;
    const diferencaDePosicao = posicaoAtual - ultimaPosicao;
    ultimaPosicao = posicaoAtual;
    if (estadoDoLayout.menuAberto || focoDentroDaNavbar) return;
    if (posicaoAtual <= Altura_Da_Zona_Do_Topo) { distanciaAcumulada = 0; definirEscondida(false); return; }
    if (diferencaDePosicao === 0) return;
    distanciaAcumulada = Math.sign(diferencaDePosicao) === Math.sign(distanciaAcumulada)
      ? distanciaAcumulada + diferencaDePosicao
      : diferencaDePosicao;
    if (distanciaAcumulada > Distancia_Minima_De_Rolagem) definirEscondida(true);
    else if (distanciaAcumulada < -Distancia_Minima_De_Rolagem) definirEscondida(false);
  };
  // requestAnimationFrame (atualiza no máximo uma vez por frame)
  window.addEventListener("scroll", () => {
    if (!atualizacaoAgendada) { atualizacaoAgendada = true; requestAnimationFrame(atualizarNavbar); }
  }, { passive: true });
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- avisos rápidos (toast) +-+-+-+-+-+-+-+-+-+-+-+-+-+-
const Tempo_Do_Aviso_Na_Tela = 3200;

// mostra um aviso no canto da tela que some sozinho
export function avisar(texto) {
  const areaDosAvisos = document.querySelector(".area-dos-avisos-rapidos");
  const aviso = criarElemento(`<div class="aviso-rapido">${icone("check")}${escaparHtml(texto)}</div>`);
  areaDosAvisos.append(aviso);
  while (areaDosAvisos.children.length > 3) areaDosAvisos.firstElementChild.remove();  // no máximo 3 na tela
  setTimeout(() => aviso.remove(), Tempo_Do_Aviso_Na_Tela);
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- janela de confirmação +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// Abre a janela de confirmação e devolve uma Promise: true se a pessoa confirmou, false se cancelou
export function pedirConfirmacao({ titulo, texto, textoConfirmar = "Confirmar", textoCancelar = "Cancelar" }) {
  return new Promise((resolver) => {
    const elementoFocadoAntes = document.activeElement;
    const fundoDaJanela = criarElemento(
      '<div class="fundo-da-janela-de-confirmacao"><div class="janela-de-confirmacao" role="alertdialog" aria-modal="true" aria-labelledby="titulo-da-janela-de-confirmacao" aria-describedby="texto-da-janela-de-confirmacao">'
      + `<h2 id="titulo-da-janela-de-confirmacao" class="subtitulo-menor">${escaparHtml(titulo)}</h2>`
      + `<div id="texto-da-janela-de-confirmacao" style="margin-top:8px"><p>${escaparHtml(texto)}</p></div>`
      + `<div class="botoes-da-janela-de-confirmacao"><button type="button" class="botao botao-secundario" data-resposta="nao">${escaparHtml(textoCancelar)}</button>`
      + `<button type="button" class="botao botao-especial" data-resposta="sim">${escaparHtml(textoConfirmar)}</button></div></div></div>`);
    const janelaDeConfirmacao = fundoDaJanela.querySelector(".janela-de-confirmacao");
    const responder = (confirmou) => {
      document.removeEventListener("keydown", aoPressionarTecla);
      fundoDaJanela.remove();
      elementoFocadoAntes?.focus?.();
      resolver(confirmou);
    };
    const aoPressionarTecla = (evento) => {
      if (evento.key === "Escape") responder(false);
      else prenderFocoNoContainer(evento, janelaDeConfirmacao);
    };
    fundoDaJanela.addEventListener("click", (evento) => { if (evento.target === fundoDaJanela) responder(false); });
    fundoDaJanela.querySelector('[data-resposta="nao"]').addEventListener("click", () => responder(false));
    fundoDaJanela.querySelector('[data-resposta="sim"]').addEventListener("click", () => responder(true));
    document.addEventListener("keydown", aoPressionarTecla);
    document.body.append(fundoDaJanela);
    fundoDaJanela.querySelector('[data-resposta="nao"]').focus();
  });
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- utilidades da página +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// muda o título da aba do navegador
export function definirTitulo(tituloDaPagina) {
  document.title = tituloDaPagina ? `${tituloDaPagina} · Fides` : "Fides";
}

// se a foto de um santo não carregar, troca pelo símbolo do Fides
function tratarImagemQuebrada(evento) {
  const imagem = evento.target;
  if (!(imagem instanceof HTMLImageElement) || !imagem.dataset.retratoDe) return;
  imagem.replaceWith(criarElemento(retratoIndisponivel(imagem.dataset.retratoDe, imagem.dataset.decorativo === "true")));
}

// Monta a moldura em volta do <main> da página e liga os comportamentos.
export function montarLayout() {
  const moduloAtual = document.body.dataset.modulo;
  const conteudoPrincipal = document.getElementById("conteudo");
  const estadoDoLayout = { menuAberto: false, mostrarNavbar: () => {} };
  conteudoPrincipal.insertAdjacentHTML("beforebegin", montarNavbar(moduloAtual) + '<div class="veu-atras-do-menu" aria-hidden="true"></div>' + montarMenuLateral(moduloAtual));
  conteudoPrincipal.insertAdjacentHTML("afterend", montarRodape());
  document.querySelector(".estrutura-do-site").insertAdjacentHTML("afterend", '<div class="area-dos-avisos-rapidos" role="status" aria-live="polite"></div>');
  ligarNavbarQueSome(estadoDoLayout);
  ligarMenuLateral(estadoDoLayout);
  document.addEventListener("error", tratarImagemQuebrada, true);
}

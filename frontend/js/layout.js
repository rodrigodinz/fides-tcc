// Moldura comum a todas as páginas: navbar, menu lateral (drawer), rodapé, avisos rápidos (toast)
// e janela de confirmação. Cada página HTML chama montarLayout() logo no começo do seu script.
import { icone } from "./componentes/icones.js";
import { ornamento, retratoIndisponivel } from "./componentes/componentes.js";
import { criarElemento, escaparHtml } from "./componentes/html.js";

// Lista única dos módulos; a navbar, o menu lateral e o rodapé são montados a partir dela.
// "chave" identifica o módulo; cada página informa a sua chave no <body data-modulo="...">.
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

// aria-current="page" marca o link da página atual (o CSS usa isso para sublinhar o link)
const marcarAtual = (modulo, moduloAtual) => (modulo.chave === moduloAtual ? ' aria-current="page" class="active"' : "");

function montarNavbar(moduloAtual) {
  const linksDaNavbar = Modulos.filter((modulo) => modulo.aparecerNaNavbar).map((modulo) =>
    `<li><a class="fd-navbar__link${modulo.chave === moduloAtual ? " active" : ""}"${modulo.chave === moduloAtual ? ' aria-current="page"' : ""} href="${modulo.endereco}">${modulo.nome}</a></li>`).join("");
  return `<header class="fd-navbar"><div class="fd-navbar__inner">`
    + `<a class="fd-navbar__simbolo" aria-label="Fides — página inicial" href="/"><img src="/imagens/simbolo-fides.svg" alt="" width="34" height="46"></a>`
    + `<a class="fd-navbar__nome" aria-hidden="true" tabindex="-1" href="/">FIDES</a>`
    + `<div class="fd-navbar__direita"><nav aria-label="Principal"><ul class="fd-navbar__links">${linksDaNavbar}</ul></nav>`
    + `<button type="button" class="fd-botao-icone" aria-label="Abrir menu" aria-expanded="false" aria-controls="fd-menu">${icone("menu")}</button>`
    + "</div></div></header>";
}

function montarDrawer(moduloAtual) {
  const linksDoMenu = Modulos.map((modulo) =>
    `<li><a${marcarAtual(modulo, moduloAtual)} href="${modulo.endereco}">${icone(modulo.icone, { tamanho: 24 })}${modulo.nome}</a></li>`).join("");
  return `<aside id="fd-menu" class="fd-drawer" role="dialog" aria-modal="true" aria-label="Menu" aria-hidden="true">`
    + `<div class="fd-drawer__topo">${ornamento("curto")}<button type="button" class="fd-botao-icone" aria-label="Fechar menu">${icone("fechar")}</button></div>`
    + `<nav class="fd-drawer__nav" aria-label="Módulos"><ul>${linksDoMenu}</ul></nav>`
    + '<div class="fd-drawer__inst"><h2>Sobre o Fides</h2>'
    + "<p>Plataforma de conteúdo e práticas católicas: santos, orações, novenas, livros e liturgia reunidos em um só lugar.</p>"
    + "<p>Trabalho de Conclusão de Curso · versão MVP. A liturgia desta versão é conteúdo de demonstração.</p></div></aside>";
}

function montarRodape() {
  const linksDoRodape = Modulos.map((modulo) => `<li><a href="${modulo.endereco}">${modulo.nome}</a></li>`).join("");
  return '<footer class="fd-rodape"><div class="fd-rodape__nav fd-escuro"><div class="fd-container fd-rodape__nav-inner">'
    + '<a class="fd-rodape__marca" href="/"><img src="/imagens/simbolo-fides.svg" alt="" width="30" height="40">FIDES</a>'
    + `<nav aria-label="Rodapé"><ul>${linksDoRodape}</ul></nav></div></div>`
    + '<div class="fd-container fd-rodape__creditos"><span>Fides · Plataforma Integrada de Conteúdo e Práticas Católicas · Trabalho de Conclusão de Curso</span>'
    + "<span>Liturgia em conteúdo de demonstração: não é o texto oficial.</span></div></footer>";
}

// ---------------------------------------------------------------- foco preso (acessibilidade)
const Seletor_De_Elementos_Focaveis = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

// com Tab, o foco gira só dentro do menu/modal aberto
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

// ---------------------------------------------------------------- menu lateral
function ligarMenuLateral(estadoDoLayout) {
  const botaoAbrir = document.querySelector('.fd-navbar button[aria-controls="fd-menu"]');
  const menu = document.getElementById("fd-menu");
  const veu = document.querySelector(".fd-veu");
  const botaoFechar = menu.querySelector('button[aria-label="Fechar menu"]');

  const aoPressionarTecla = (evento) => {
    if (evento.key === "Escape") { evento.preventDefault(); fecharMenu(); }
    else prenderFocoNoContainer(evento, menu);
  };
  function abrirMenu() {
    estadoDoLayout.menuAberto = true;
    menu.classList.add("is-aberto");
    veu.classList.add("is-aberto");
    menu.setAttribute("aria-hidden", "false");
    botaoAbrir.setAttribute("aria-expanded", "true");
    document.body.classList.add("fd-sem-rolagem");  // trava a rolagem da página atrás do menu
    document.addEventListener("keydown", aoPressionarTecla);
    estadoDoLayout.mostrarNavbar();
    setTimeout(() => botaoFechar.focus(), 30);
  }
  function fecharMenu() {
    estadoDoLayout.menuAberto = false;
    menu.classList.remove("is-aberto");
    veu.classList.remove("is-aberto");
    menu.setAttribute("aria-hidden", "true");
    botaoAbrir.setAttribute("aria-expanded", "false");
    document.body.classList.remove("fd-sem-rolagem");
    document.removeEventListener("keydown", aoPressionarTecla);
    setTimeout(() => botaoAbrir.focus(), 0);  // devolve o foco ao botão que abriu o menu
  }
  botaoAbrir.addEventListener("click", abrirMenu);
  botaoFechar.addEventListener("click", fecharMenu);
  veu.addEventListener("click", fecharMenu);
}

// ---------------------------------------------------------------- navbar que some ao rolar
export const Distancia_Minima_De_Rolagem = 24;
export const Altura_Da_Zona_Do_Topo = 16;

// esconde a navbar quando a pessoa rola para baixo e mostra de novo ao rolar para cima
function ligarNavbarQueSome(estadoDoLayout) {
  const navbar = document.querySelector(".fd-navbar");
  let focoDentroDaNavbar = false;
  let ultimaPosicao = window.scrollY;
  let distanciaAcumulada = 0;
  let atualizacaoAgendada = false;
  const definirEscondida = (escondida) => navbar.classList.toggle("is-escondida", escondida);
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
  // requestAnimationFrame: atualiza no máximo uma vez por quadro, sem pesar a rolagem
  window.addEventListener("scroll", () => {
    if (!atualizacaoAgendada) { atualizacaoAgendada = true; requestAnimationFrame(atualizarNavbar); }
  }, { passive: true });
}

// ---------------------------------------------------------------- avisos rápidos (toast)
const Tempo_Do_Aviso_Na_Tela = 3200;

// mostra um aviso no canto da tela que some sozinho; aria-live faz o leitor de tela ler o aviso
export function avisar(texto) {
  const areaDosAvisos = document.querySelector(".fd-toasts");
  const aviso = criarElemento(`<div class="fd-toast">${icone("check")}${escaparHtml(texto)}</div>`);
  areaDosAvisos.append(aviso);
  while (areaDosAvisos.children.length > 3) areaDosAvisos.firstElementChild.remove();  // no máximo 3 na tela
  setTimeout(() => aviso.remove(), Tempo_Do_Aviso_Na_Tela);
}

// ---------------------------------------------------------------- janela de confirmação
// Abre o modal e devolve uma Promise: true se a pessoa confirmou, false se cancelou.
// Esc cancela, clicar fora cancela e o foco fica preso dentro do modal enquanto ele está aberto.
export function pedirConfirmacao({ titulo, texto, textoConfirmar = "Confirmar", textoCancelar = "Cancelar" }) {
  return new Promise((resolver) => {
    const elementoFocadoAntes = document.activeElement;
    const veuDoModal = criarElemento(
      '<div class="fd-modal-veu"><div class="fd-modal" role="alertdialog" aria-modal="true" aria-labelledby="fd-modal-titulo" aria-describedby="fd-modal-texto">'
      + `<h2 id="fd-modal-titulo" class="fd-h4">${escaparHtml(titulo)}</h2>`
      + `<div id="fd-modal-texto" style="margin-top:8px"><p>${escaparHtml(texto)}</p></div>`
      + `<div class="fd-modal__acoes"><button type="button" class="fd-btn fd-btn--secundario" data-resposta="nao">${escaparHtml(textoCancelar)}</button>`
      + `<button type="button" class="fd-btn fd-btn--especial" data-resposta="sim">${escaparHtml(textoConfirmar)}</button></div></div></div>`);
    const modal = veuDoModal.querySelector(".fd-modal");
    const responder = (confirmou) => {
      document.removeEventListener("keydown", aoPressionarTecla);
      veuDoModal.remove();
      elementoFocadoAntes?.focus?.();
      resolver(confirmou);
    };
    const aoPressionarTecla = (evento) => {
      if (evento.key === "Escape") responder(false);
      else prenderFocoNoContainer(evento, modal);
    };
    veuDoModal.addEventListener("click", (evento) => { if (evento.target === veuDoModal) responder(false); });
    veuDoModal.querySelector('[data-resposta="nao"]').addEventListener("click", () => responder(false));
    veuDoModal.querySelector('[data-resposta="sim"]').addEventListener("click", () => responder(true));
    document.addEventListener("keydown", aoPressionarTecla);
    document.body.append(veuDoModal);
    veuDoModal.querySelector('[data-resposta="nao"]').focus();
  });
}

// ---------------------------------------------------------------- utilidades da página
// muda o título da aba do navegador
export function definirTitulo(tituloDaPagina) {
  document.title = tituloDaPagina ? `${tituloDaPagina} · Fides` : "Fides";
}

// se a foto de um santo não carregar, troca pelo símbolo do Fides
// (o "true" no fim escuta na fase de captura, porque o evento de erro de imagem não sobe pela página)
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
  conteudoPrincipal.insertAdjacentHTML("beforebegin", montarNavbar(moduloAtual) + '<div class="fd-veu" aria-hidden="true"></div>' + montarDrawer(moduloAtual));
  conteudoPrincipal.insertAdjacentHTML("afterend", montarRodape());
  document.querySelector(".fd-app").insertAdjacentHTML("afterend", '<div class="fd-toasts" role="status" aria-live="polite"></div>');
  ligarNavbarQueSome(estadoDoLayout);
  ligarMenuLateral(estadoDoLayout);
  document.addEventListener("error", tratarImagemQuebrada, true);
}

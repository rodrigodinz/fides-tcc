import { buscarJsonNaApi } from "./cliente.js";
import { Limite_Maximo_Por_Pagina } from "./config.js";

const montarParametrosDePaginacao = (pagina = 1, limite = Limite_Maximo_Por_Pagina) => ({ pagina, limite });

// Um objeto por módulo da API. Cada função chama uma rota do back-end;
// as páginas só usam estas funções e nunca montam URL na mão.
export const servicoSantos = {
  listarSantos: ({ pagina, limite, nome } = {}, opcoes) =>
    buscarJsonNaApi("/santos", { ...montarParametrosDePaginacao(pagina, limite), nome: nome?.trim() || undefined }, opcoes),
  detalharSanto: (santoId, opcoes) => buscarJsonNaApi(`/santos/${encodeURIComponent(santoId)}`, {}, opcoes),
};

export const servicoOracoes = {
  listarOracoes: ({ pagina, limite, basica, momento_id, santo_id } = {}, opcoes) =>
    buscarJsonNaApi("/oracoes", { ...montarParametrosDePaginacao(pagina, limite), basica, momento_id, santo_id }, opcoes),
  listarMomentosDoDia: (opcoes) => buscarJsonNaApi("/momentos", {}, opcoes),
};

export const servicoNovenas = {
  listarNovenas: ({ pagina, limite, santo_id } = {}, opcoes) =>
    buscarJsonNaApi("/novenas", { ...montarParametrosDePaginacao(pagina, limite), santo_id }, opcoes),
  detalharNovena: (novenaId, opcoes) => buscarJsonNaApi(`/novenas/${encodeURIComponent(novenaId)}`, {}, opcoes),
  listarDiasDaNovena: (novenaId, opcoes) => buscarJsonNaApi(`/novenas/${encodeURIComponent(novenaId)}/dias`, {}, opcoes),
  verDiaDaNovena: (novenaId, numeroDoDia, opcoes) =>
    buscarJsonNaApi(`/novenas/${encodeURIComponent(novenaId)}/dias/${encodeURIComponent(numeroDoDia)}`, {}, opcoes),
};

export const servicoLivros = {
  listarLivros: ({ pagina, limite, santo_id } = {}, opcoes) =>
    buscarJsonNaApi("/livros", { ...montarParametrosDePaginacao(pagina, limite), santo_id }, opcoes),
  detalharLivro: (livroId, opcoes) => buscarJsonNaApi(`/livros/${encodeURIComponent(livroId)}`, {}, opcoes),
  // sem santo visitado nem chama a API (ela responderia 422)
  listarLivrosRecomendados: (idsDosSantos, { pagina, limite } = {}, opcoes) => {
    if (!Array.isArray(idsDosSantos) || idsDosSantos.length === 0) {
      return Promise.reject(new Error("listarLivrosRecomendados() exige ao menos um santo acessado."));
    }
    return buscarJsonNaApi("/livros/recomendados", { ...montarParametrosDePaginacao(pagina, limite), santo_id: idsDosSantos }, opcoes);
  },
};

export const servicoLiturgia = {
  verLiturgiaDoDia: (data, opcoes) => buscarJsonNaApi("/liturgia/dia", { data }, opcoes),
  verLiturgiaDasHoras: (data, bloco, opcoes) => buscarJsonNaApi("/liturgia/horas", { data, bloco }, opcoes),
};

export const servicoAgenda = {
  verConteudosDoDia: (data, opcoes) => buscarJsonNaApi("/agenda", { data }, opcoes),
};

export const servicoSaude = {
  verificarSaude: (opcoes) => buscarJsonNaApi("/health", {}, { ...opcoes, prefixo: "" }),
};

// percorre página por página até acabar; usado para encher os filtros de santo
export async function listarTodasAsPaginas(funcaoDeListagem, filtros = {}, opcoes) {
  const todosOsItens = [];
  let pagina = 1;
  for (;;) {
    const respostaDaPagina = await funcaoDeListagem({ ...filtros, pagina, limite: Limite_Maximo_Por_Pagina }, opcoes);
    todosOsItens.push(...respostaDaPagina.itens);
    if (pagina >= respostaDaPagina.total_paginas || respostaDaPagina.itens.length === 0) break;
    pagina += 1;
  }
  return todosOsItens;
}

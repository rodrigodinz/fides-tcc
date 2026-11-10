/**
 * Serviços por domínio: um método por rota GET da API 0.2.0.
 * Paginação sempre com `pagina` e `limite` (1–20). Nenhum campo é inventado aqui.
 */
import { obterJson } from "./cliente.js";
import { LIMITE_MAXIMO } from "./config.js";

const pag = (pagina = 1, limite = LIMITE_MAXIMO) => ({ pagina, limite });

export const santos = {
  listar: ({ pagina, limite, q } = {}, opcoes) => obterJson("/santos", { ...pag(pagina, limite), q: q?.trim() || undefined }, opcoes),
  detalhar: (id, opcoes) => obterJson(`/santos/${encodeURIComponent(id)}`, {}, opcoes),
};

export const oracoes = {
  listar: ({ pagina, limite, basica, momento_id, santo_id } = {}, opcoes) =>
    obterJson("/oracoes", { ...pag(pagina, limite), basica, momento_id, santo_id }, opcoes),
  momentos: (opcoes) => obterJson("/momentos", {}, opcoes),
};

export const novenas = {
  listar: ({ pagina, limite, santo_id } = {}, opcoes) => obterJson("/novenas", { ...pag(pagina, limite), santo_id }, opcoes),
  detalhar: (id, opcoes) => obterJson(`/novenas/${encodeURIComponent(id)}`, {}, opcoes),
  dias: (id, opcoes) => obterJson(`/novenas/${encodeURIComponent(id)}/dias`, {}, opcoes),
  dia: (id, numero, opcoes) => obterJson(`/novenas/${encodeURIComponent(id)}/dias/${encodeURIComponent(numero)}`, {}, opcoes),
};

export const livros = {
  listar: ({ pagina, limite, santo_id } = {}, opcoes) => obterJson("/livros", { ...pag(pagina, limite), santo_id }, opcoes),
  detalhar: (id, opcoes) => obterJson(`/livros/${encodeURIComponent(id)}`, {}, opcoes),
  /** Exige ao menos um id (sem ids a API responde 422): o chamador não deve chamar com lista vazia. */
  recomendados: (santoIds, { pagina, limite } = {}, opcoes) => {
    if (!Array.isArray(santoIds) || santoIds.length === 0) {
      return Promise.reject(new Error("recomendados() exige ao menos um santo acessado."));
    }
    return obterJson("/livros/recomendados", { ...pag(pagina, limite), santo_id: santoIds }, opcoes);
  },
};

export const liturgia = {
  dia: (data, opcoes) => obterJson("/liturgia/dia", { data }, opcoes),
  horas: (data, bloco, opcoes) => obterJson("/liturgia/horas", { data, bloco }, opcoes),
};

export const agenda = {
  doDia: (data, opcoes) => obterJson("/agenda", { data }, opcoes),
};

export const saude = {
  verificar: (opcoes) => obterJson("/health", {}, { ...opcoes, prefixo: "" }),
};

/** Busca todas as páginas de uma listagem (para preencher dropdowns, ex.: santos). */
export async function listarTudo(listar, filtros = {}, opcoes) {
  const itens = [];
  let pagina = 1;
  for (;;) {
    const resp = await listar({ ...filtros, pagina, limite: LIMITE_MAXIMO }, opcoes);
    itens.push(...resp.itens);
    if (pagina >= resp.total_paginas || resp.itens.length === 0) break;
    pagina += 1;
  }
  return itens;
}

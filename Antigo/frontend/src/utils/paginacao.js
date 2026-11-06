/** Páginas visíveis: a atual, até duas antes e duas depois, só as que existem. */
export function paginasVisiveis(atual, total) {
  if (!Number.isInteger(total) || total < 1) return [];
  const a = Math.min(Math.max(1, atual), total);
  const lista = [];
  for (let n = a - 2; n <= a + 2; n += 1) if (n >= 1 && n <= total) lista.push(n);
  return lista;
}

/** Lê ?pagina= da URL com segurança (inteiro >= 1). */
export function lerPagina(valor) {
  const n = Number(valor);
  return Number.isInteger(n) && n >= 1 ? n : 1;
}

export function lerId(valor) {
  const n = Number(valor);
  return Number.isInteger(n) && n >= 1 ? n : null;
}

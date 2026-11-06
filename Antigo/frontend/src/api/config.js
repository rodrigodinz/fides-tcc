/**
 * Origem da API REST do Fides, configurável por ambiente (VITE_API_URL).
 * A API não monta URLs absolutas de imagem: foto_url é um caminho relativo
 * (ex.: /static/santos/tomas-de-aquino.jpg) que o front-end prefixa com a origem.
 */
const PADRAO = "http://127.0.0.1:8000";

export function normalizarOrigem(valor) {
  const texto = typeof valor === "string" ? valor.trim() : "";
  return (texto || PADRAO).replace(/\/+$/, "");
}

export const API_ORIGEM = normalizarOrigem(import.meta.env.VITE_API_URL);
export const PREFIXO_API = "/api/v1";
export const LIMITE_MAXIMO = 20;

/** URL absoluta de uma imagem servida pela API; null se o caminho for vazio. */
export function urlImagem(caminho, origem = API_ORIGEM) {
  if (typeof caminho !== "string" || caminho.trim() === "") return null;
  if (/^https?:\/\//i.test(caminho)) return caminho;
  const relativo = caminho.startsWith("/") ? caminho : `/${caminho}`;
  return `${origem}${relativo}`;
}

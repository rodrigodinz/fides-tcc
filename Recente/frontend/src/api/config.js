const Origem_Padrao_Da_Api = "http://127.0.0.1:8000";

export function normalizarOrigem(valorDaOrigem) {
  const textoDaOrigem = typeof valorDaOrigem === "string" ? valorDaOrigem.trim() : "";
  return (textoDaOrigem || Origem_Padrao_Da_Api).replace(/\/+$/, "");
}

// endereço da API vem do arquivo .env (VITE_API_URL); sem ele usa http://127.0.0.1:8000
export const Origem_Da_Api = normalizarOrigem(import.meta.env.VITE_API_URL);
export const Prefixo_Da_Api = "/api/v1";
export const Limite_Maximo_Por_Pagina = 20;

// a API devolve a foto como caminho relativo (/static/...); aqui vira URL completa
export function montarUrlDaImagem(caminhoDaImagem, origem = Origem_Da_Api) {
  if (typeof caminhoDaImagem !== "string" || caminhoDaImagem.trim() === "") return null;
  if (/^https?:\/\//i.test(caminhoDaImagem)) return caminhoDaImagem;
  const caminhoRelativo = caminhoDaImagem.startsWith("/") ? caminhoDaImagem : `/${caminhoDaImagem}`;
  return `${origem}${caminhoRelativo}`;
}

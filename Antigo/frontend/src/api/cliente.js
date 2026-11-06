/**
 * Cliente HTTP único do Fides. Centraliza origem, montagem de URL e query params,
 * tempo limite e o formato de erro da API: {erro: {codigo, mensagem, detalhes}}.
 * Só faz GET: o MVP não tem rotas de escrita.
 */
import { API_ORIGEM, PREFIXO_API } from "./config.js";

export const TEMPO_LIMITE_MS = 12000;

export class ErroApi extends Error {
  constructor({ codigo, mensagem, status = 0, detalhes = [] }) {
    super(mensagem || codigo);
    this.name = "ErroApi";
    this.codigo = codigo;
    this.status = status;
    this.detalhes = Array.isArray(detalhes) ? detalhes : [];
  }
}

/** Monta a URL: ignora null/undefined/"" e repete o parâmetro para listas. */
export function montarUrl(caminho, params = {}, { origem = API_ORIGEM, prefixo = PREFIXO_API } = {}) {
  const busca = new URLSearchParams();
  for (const [chave, valor] of Object.entries(params)) {
    const valores = Array.isArray(valor) ? valor : [valor];
    for (const v of valores) {
      if (v === null || v === undefined || v === "") continue;
      busca.append(chave, String(v));
    }
  }
  const qs = busca.toString();
  return `${origem}${prefixo}${caminho}${qs ? `?${qs}` : ""}`;
}

async function lerErro(resposta) {
  try {
    const corpo = await resposta.json();
    if (corpo && corpo.erro && typeof corpo.erro.codigo === "string") {
      return new ErroApi({ ...corpo.erro, status: resposta.status });
    }
  } catch {
    /* corpo não é JSON: cai no genérico abaixo */
  }
  const codigo = resposta.status === 503 ? "SERVICO_INDISPONIVEL" : resposta.status === 404 ? "ROTA_NAO_ENCONTRADA" : "ERRO_INTERNO";
  return new ErroApi({ codigo, mensagem: "Resposta inesperada do servidor.", status: resposta.status });
}

/**
 * GET JSON. Lança ErroApi (códigos da API, FALHA_DE_REDE ou TEMPO_ESGOTADO)
 * ou DOMException AbortError quando o chamador cancela (troca de página/filtro).
 */
export async function obterJson(caminho, params, { signal, tempoLimite = TEMPO_LIMITE_MS, prefixo, origem, fetchImpl } = {}) {
  const url = montarUrl(caminho, params, { prefixo: prefixo ?? PREFIXO_API, origem: origem ?? API_ORIGEM });
  const controle = new AbortController();
  let esgotou = false;
  const timer = setTimeout(() => { esgotou = true; controle.abort(); }, tempoLimite);
  const repassar = () => controle.abort();
  if (signal) {
    if (signal.aborted) controle.abort();
    else signal.addEventListener("abort", repassar, { once: true });
  }
  const executar = fetchImpl ?? globalThis.fetch;
  try {
    let resposta;
    try {
      resposta = await executar(url, { method: "GET", headers: { Accept: "application/json" }, signal: controle.signal });
    } catch (e) {
      if (esgotou) throw new ErroApi({ codigo: "TEMPO_ESGOTADO", mensagem: "O servidor demorou demais para responder." });
      if (signal?.aborted) throw new DOMException("Consulta cancelada.", "AbortError");
      throw new ErroApi({ codigo: "FALHA_DE_REDE", mensagem: e?.message || "Falha de rede." });
    }
    if (!resposta.ok) throw await lerErro(resposta);
    try {
      return await resposta.json();
    } catch {
      throw new ErroApi({ codigo: "ERRO_INTERNO", mensagem: "Resposta inválida do servidor.", status: resposta.status });
    }
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", repassar);
  }
}

export function ehCancelamento(erro) {
  return erro?.name === "AbortError";
}

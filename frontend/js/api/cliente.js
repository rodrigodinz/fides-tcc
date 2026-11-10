// A API e as páginas são servidas pelo mesmo uvicorn, então os endereços são relativos (sem http://...)
export const Prefixo_Da_Api = "/api/v1";
export const Limite_Maximo_Por_Pagina = 20;
export const Tempo_Limite_Em_Milissegundos = 12000;

// erro padronizado do front: guarda o código que a API mandou (ex.: RECURSO_NAO_ENCONTRADO)
export class ErroDaApi extends Error {
  constructor({ codigo, mensagem, status = 0, detalhes = [] }) {
    super(mensagem || codigo);
    this.name = "ErroDaApi";
    this.codigo = codigo;
    this.status = status;
    this.detalhes = Array.isArray(detalhes) ? detalhes : [];
  }
}

// monta a URL com os parâmetros (?pagina=1&limite=20); ignora vazios e repete listas (santo_id=1&santo_id=2)
export function montarUrlDaRequisicao(caminho, parametros = {}, prefixo = Prefixo_Da_Api) {
  const parametrosDaUrl = new URLSearchParams();
  for (const [nomeDoParametro, valorDoParametro] of Object.entries(parametros)) {
    const valores = Array.isArray(valorDoParametro) ? valorDoParametro : [valorDoParametro];
    for (const valor of valores) {
      if (valor === null || valor === undefined || valor === "") continue;
      parametrosDaUrl.append(nomeDoParametro, String(valor));
    }
  }
  const textoDosParametros = parametrosDaUrl.toString();
  return `${prefixo}${caminho}${textoDosParametros ? `?${textoDosParametros}` : ""}`;
}

// a foto vem da API como caminho relativo (/static/santos/x.jpg)
export function montarUrlDaImagem(caminhoDaImagem) {
  if (typeof caminhoDaImagem !== "string" || caminhoDaImagem.trim() === "") return null;
  if (/^https?:\/\//i.test(caminhoDaImagem)) return caminhoDaImagem;
  return caminhoDaImagem.startsWith("/") ? caminhoDaImagem : `/${caminhoDaImagem}`;
}

async function lerErroDaResposta(resposta) {
  const corpoDaResposta = await resposta.json().catch(() => null);
  if (corpoDaResposta?.erro && typeof corpoDaResposta.erro.codigo === "string") {
    return new ErroDaApi({ ...corpoDaResposta.erro, status: resposta.status });
  }
  const codigo = resposta.status === 503 ? "SERVICO_INDISPONIVEL" : resposta.status === 404 ? "ROTA_NAO_ENCONTRADA" : "ERRO_INTERNO";
  return new ErroDaApi({ codigo, mensagem: "Resposta inesperada do servidor.", status: resposta.status });
}

// Única função que faz fetch na API. Ela:
// - cancela a requisição se demorar mais que 12 s;
// - transforma falha de rede, tempo esgotado e erros HTTP em ErroDaApi;
// - devolve o JSON quando dá certo.
export async function buscarJsonNaApi(caminho, parametros, { signal, tempoLimite = Tempo_Limite_Em_Milissegundos, prefixo } = {}) {
  const url = montarUrlDaRequisicao(caminho, parametros, prefixo ?? Prefixo_Da_Api);
  // AbortController permite cancelar o fetch (por tempo esgotado ou quando a pessoa muda o filtro)
  const controladorDeCancelamento = new AbortController();
  let tempoEsgotado = false;
  const temporizador = setTimeout(() => { tempoEsgotado = true; controladorDeCancelamento.abort(); }, tempoLimite);
  const repassarCancelamento = () => controladorDeCancelamento.abort();
  if (signal) {
    if (signal.aborted) controladorDeCancelamento.abort();
    else signal.addEventListener("abort", repassarCancelamento, { once: true });
  }
  try {
    let resposta;
    try {
      resposta = await fetch(url, { method: "GET", headers: { Accept: "application/json" }, signal: controladorDeCancelamento.signal });
    } catch (erroDeRede) {
      if (tempoEsgotado) throw new ErroDaApi({ codigo: "TEMPO_ESGOTADO", mensagem: "O servidor demorou demais para responder." });
      if (signal?.aborted) throw new DOMException("Consulta cancelada.", "AbortError");
      throw new ErroDaApi({ codigo: "FALHA_DE_REDE", mensagem: erroDeRede?.message || "Falha de rede." });
    }
    if (!resposta.ok) throw await lerErroDaResposta(resposta);
    try {
      return await resposta.json();
    } catch {
      throw new ErroDaApi({ codigo: "ERRO_INTERNO", mensagem: "Resposta inválida do servidor.", status: resposta.status });
    }
  } finally {
    clearTimeout(temporizador);
    signal?.removeEventListener("abort", repassarCancelamento);
  }
}

export function ehCancelamentoDaConsulta(erro) {
  return erro?.name === "AbortError";
}

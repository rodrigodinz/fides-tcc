import { ErroDaApi, montarUrlDaRequisicao, buscarJsonNaApi } from "./cliente.js";
import { normalizarOrigem, montarUrlDaImagem } from "./config.js";
import { servicoLivros, listarTodasAsPaginas } from "./servicos.js";
import { instalarFetchFalso, montarRespostaJson } from "../testes/fetchFalso.js";

const Origem_E_Prefixo_De_Teste = { origem: "http://api", prefixo: "/api/v1" };

describe("montarUrlDaRequisicao", () => {
  it("usa pagina e limite e ignora valores vazios", () => {
    expect(montarUrlDaRequisicao("/santos", { pagina: 1, limite: 20, nome: "", x: null, y: undefined }, Origem_E_Prefixo_De_Teste)).toBe("http://api/api/v1/santos?pagina=1&limite=20");
  });
  it("repete o parâmetro para listas (santo_id)", () => {
    expect(montarUrlDaRequisicao("/livros/recomendados", { santo_id: [2, 5] }, Origem_E_Prefixo_De_Teste)).toBe("http://api/api/v1/livros/recomendados?santo_id=2&santo_id=5");
  });
  it("mantém basica=false (filtro válido)", () => {
    expect(montarUrlDaRequisicao("/oracoes", { basica: false }, Origem_E_Prefixo_De_Teste)).toContain("basica=false");
  });
});

describe("origem e imagens", () => {
  it("remove barra final e usa o padrão quando ausente", () => {
    expect(normalizarOrigem("http://x:8000/")).toBe("http://x:8000");
    expect(normalizarOrigem(undefined)).toBe("http://127.0.0.1:8000");
  });
  it("concatena foto_url relativa e trata nulo/vazio", () => {
    expect(montarUrlDaImagem("/static/santos/a.jpg", "http://api")).toBe("http://api/static/santos/a.jpg");
    expect(montarUrlDaImagem(null)).toBeNull();
    expect(montarUrlDaImagem("  ")).toBeNull();
  });
});

describe("buscarJsonNaApi", () => {
  it("devolve o JSON em caso de sucesso", async () => {
    instalarFetchFalso([["/health", { status: "ok" }]]);
    await expect(buscarJsonNaApi("/health", {}, { prefixo: "" })).resolves.toEqual({ status: "ok" });
  });
  it("lê o envelope de erro da API", async () => {
    instalarFetchFalso([["/santos/9", () => montarRespostaJson({ erro: { codigo: "RECURSO_NAO_ENCONTRADO", mensagem: "Santo não encontrado(a).", detalhes: [] } }, 404)]]);
    const erroRecebido = await buscarJsonNaApi("/santos/9").catch((erro) => erro);
    expect(erroRecebido).toBeInstanceOf(ErroDaApi);
    expect(erroRecebido.codigo).toBe("RECURSO_NAO_ENCONTRADO");
    expect(erroRecebido.status).toBe(404);
  });
  it("transforma falha de rede em FALHA_DE_REDE", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))));
    await expect(buscarJsonNaApi("/santos")).rejects.toMatchObject({ codigo: "FALHA_DE_REDE" });
  });
  it("resposta 503 sem JSON vira SERVICO_INDISPONIVEL", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("<html>", { status: 503 }))));
    await expect(buscarJsonNaApi("/santos")).rejects.toMatchObject({ codigo: "SERVICO_INDISPONIVEL" });
  });
  it("cancelamento do chamador vira AbortError (não é erro de tela)", async () => {
    vi.stubGlobal("fetch", vi.fn((_url, { signal }) => new Promise((_resolver, rejeitar) => signal.addEventListener("abort", () => rejeitar(new DOMException("a", "AbortError"))))));
    const controladorDeCancelamento = new AbortController();
    const consulta = buscarJsonNaApi("/santos", {}, { signal: controladorDeCancelamento.signal });
    controladorDeCancelamento.abort();
    await expect(consulta).rejects.toMatchObject({ name: "AbortError" });
  });
  it("só usa GET", async () => {
    const fetchFalso = vi.fn(() => montarRespostaJson({}));
    vi.stubGlobal("fetch", fetchFalso);
    await buscarJsonNaApi("/momentos");
    expect(fetchFalso.mock.calls[0][1].method).toBe("GET");
  });
});

describe("serviços", () => {
  it("livros recomendados sem ids não chama a API (ela responderia 422)", async () => {
    const fetchFalso = vi.fn();
    vi.stubGlobal("fetch", fetchFalso);
    await expect(servicoLivros.listarLivrosRecomendados([])).rejects.toThrow();
    expect(fetchFalso).not.toHaveBeenCalled();
  });
  it("listarTodasAsPaginas percorre todas as páginas", async () => {
    const listarPagina = vi.fn(({ pagina }) => Promise.resolve({ itens: [pagina], pagina, limite: 20, total_registros_filtros: 2, total_paginas: 2 }));
    await expect(listarTodasAsPaginas(listarPagina)).resolves.toEqual([1, 2]);
    expect(listarPagina).toHaveBeenCalledTimes(2);
  });
});

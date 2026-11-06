import { ErroApi, montarUrl, obterJson } from "./cliente.js";
import { normalizarOrigem, urlImagem } from "./config.js";
import { livros, listarTudo } from "./servicos.js";
import { instalarFetch, respostaJson } from "../testes/fetchFalso.js";

const O = { origem: "http://api", prefixo: "/api/v1" };

describe("montarUrl", () => {
  it("usa pagina e limite e ignora valores vazios", () => {
    expect(montarUrl("/santos", { pagina: 1, limite: 20, q: "", x: null, y: undefined }, O)).toBe("http://api/api/v1/santos?pagina=1&limite=20");
  });
  it("repete o parâmetro para listas (santo_id)", () => {
    expect(montarUrl("/livros/recomendados", { santo_id: [2, 5] }, O)).toBe("http://api/api/v1/livros/recomendados?santo_id=2&santo_id=5");
  });
  it("mantém basica=false (filtro válido)", () => {
    expect(montarUrl("/oracoes", { basica: false }, O)).toContain("basica=false");
  });
});

describe("origem e imagens", () => {
  it("remove barra final e usa o padrão quando ausente", () => {
    expect(normalizarOrigem("http://x:8000/")).toBe("http://x:8000");
    expect(normalizarOrigem(undefined)).toBe("http://127.0.0.1:8000");
  });
  it("concatena foto_url relativa e trata nulo/vazio", () => {
    expect(urlImagem("/static/santos/a.jpg", "http://api")).toBe("http://api/static/santos/a.jpg");
    expect(urlImagem(null)).toBeNull();
    expect(urlImagem("  ")).toBeNull();
  });
});

describe("obterJson", () => {
  it("devolve o JSON em caso de sucesso", async () => {
    instalarFetch([["/health", { status: "ok" }]]);
    await expect(obterJson("/health", {}, { prefixo: "" })).resolves.toEqual({ status: "ok" });
  });
  it("lê o envelope de erro da API", async () => {
    instalarFetch([["/santos/9", () => respostaJson({ erro: { codigo: "RECURSO_NAO_ENCONTRADO", mensagem: "Santo não encontrado(a).", detalhes: [] } }, 404)]]);
    const e = await obterJson("/santos/9").catch((x) => x);
    expect(e).toBeInstanceOf(ErroApi);
    expect(e.codigo).toBe("RECURSO_NAO_ENCONTRADO");
    expect(e.status).toBe(404);
  });
  it("transforma falha de rede em FALHA_DE_REDE", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new TypeError("Failed to fetch"))));
    await expect(obterJson("/santos")).rejects.toMatchObject({ codigo: "FALHA_DE_REDE" });
  });
  it("resposta 503 sem JSON vira SERVICO_INDISPONIVEL", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(new Response("<html>", { status: 503 }))));
    await expect(obterJson("/santos")).rejects.toMatchObject({ codigo: "SERVICO_INDISPONIVEL" });
  });
  it("cancelamento do chamador vira AbortError (não é erro de tela)", async () => {
    vi.stubGlobal("fetch", vi.fn((_u, { signal }) => new Promise((_r, rej) => signal.addEventListener("abort", () => rej(new DOMException("a", "AbortError"))))));
    const c = new AbortController();
    const p = obterJson("/santos", {}, { signal: c.signal });
    c.abort();
    await expect(p).rejects.toMatchObject({ name: "AbortError" });
  });
  it("só usa GET", async () => {
    const f = vi.fn(() => respostaJson({}));
    vi.stubGlobal("fetch", f);
    await obterJson("/momentos");
    expect(f.mock.calls[0][1].method).toBe("GET");
  });
});

describe("serviços", () => {
  it("recomendados sem ids não chama a API (ela responderia 422)", async () => {
    const f = vi.fn();
    vi.stubGlobal("fetch", f);
    await expect(livros.recomendados([])).rejects.toThrow();
    expect(f).not.toHaveBeenCalled();
  });
  it("listarTudo percorre todas as páginas", async () => {
    const listar = vi.fn(({ pagina }) => Promise.resolve({ itens: [pagina], pagina, limite: 20, total: 2, total_paginas: 2 }));
    await expect(listarTudo(listar)).resolves.toEqual([1, 2]);
    expect(listar).toHaveBeenCalledTimes(2);
  });
});

import { listarSantosAcessados, registrarSantoAcessado, MAXIMO_SANTOS } from "./santosAcessados.js";
import { alternarMarcado, lerNovenaPessoal, salvarNovenaPessoal } from "./novenaPessoal.js";
import { gravarJson, lerJson, PREFIXO } from "./armazenamento.js";

beforeEach(() => localStorage.clear());

describe("santos acessados", () => {
  it("deduplica e coloca o mais recente na frente", () => {
    registrarSantoAcessado(2); registrarSantoAcessado(5); registrarSantoAcessado(2);
    expect(listarSantosAcessados()).toEqual([2, 5]);
  });
  it("guarda no máximo 20 ids válidos", () => {
    for (let i = 1; i <= 30; i++) registrarSantoAcessado(i);
    const l = listarSantosAcessados();
    expect(l).toHaveLength(MAXIMO_SANTOS);
    expect(l[0]).toBe(30);
  });
  it("ignora ids inválidos e dados corrompidos", () => {
    registrarSantoAcessado("abc"); registrarSantoAcessado(-1); registrarSantoAcessado(1.5);
    expect(listarSantosAcessados()).toEqual([]);
    localStorage.setItem(`${PREFIXO}santos-acessados`, "{não é json");
    expect(listarSantosAcessados()).toEqual([]);
    localStorage.setItem(`${PREFIXO}santos-acessados`, JSON.stringify([3, "4", 0, null, 3]));
    expect(listarSantosAcessados()).toEqual([3, 4]);
  });
});

describe("novena pessoal", () => {
  it("normaliza dias fora de 1..9 e tipos errados", () => {
    gravarJson("novena:1", { marcados: [3, 3, 0, 12, "2", 1], pedidos: 42 });
    expect(lerNovenaPessoal(1)).toEqual({ marcados: [1, 3], pedidos: "" });
  });
  it("alterna marcação e persiste só no dispositivo", () => {
    const d = alternarMarcado({ marcados: [], pedidos: "" }, 4);
    expect(salvarNovenaPessoal(7, d).ok).toBe(true);
    expect(lerNovenaPessoal(7).marcados).toEqual([4]);
    expect(alternarMarcado(lerNovenaPessoal(7), 4).marcados).toEqual([]);
  });
  it("sem conteúdo remove a chave", () => {
    salvarNovenaPessoal(8, { marcados: [1], pedidos: "x" });
    salvarNovenaPessoal(8, { marcados: [], pedidos: "" });
    expect(localStorage.getItem(`${PREFIXO}novena:8`)).toBeNull();
  });
  it("armazenamento indisponível não quebra", () => {
    const original = Storage.prototype.setItem;
    Storage.prototype.setItem = () => { throw new Error("QuotaExceededError"); };
    try {
      expect(gravarJson("x", 1)).toBe(false);
      expect(lerJson("x", "padrão")).toBe("padrão");
      expect(salvarNovenaPessoal(9, { marcados: [1], pedidos: "" }).ok).toBe(false);
    } finally { Storage.prototype.setItem = original; }
  });
});

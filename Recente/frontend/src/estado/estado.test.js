import { listarSantosAcessados, registrarSantoAcessado, Maximo_De_Santos_Acessados } from "./santosAcessados.js";
import { alternarDiaMarcado, lerNovenaPessoal, salvarNovenaPessoal } from "./novenaPessoal.js";
import { gravarJsonNoDispositivo, lerJsonDoDispositivo, Prefixo_Das_Chaves } from "./armazenamento.js";

beforeEach(() => localStorage.clear());

describe("santos acessados", () => {
  it("deduplica e coloca o mais recente na frente", () => {
    registrarSantoAcessado(2); registrarSantoAcessado(5); registrarSantoAcessado(2);
    expect(listarSantosAcessados()).toEqual([2, 5]);
  });
  it("guarda no máximo 20 ids válidos", () => {
    for (let santoId = 1; santoId <= 30; santoId++) registrarSantoAcessado(santoId);
    const santosAcessados = listarSantosAcessados();
    expect(santosAcessados).toHaveLength(Maximo_De_Santos_Acessados);
    expect(santosAcessados[0]).toBe(30);
  });
  it("ignora ids inválidos e dados corrompidos", () => {
    registrarSantoAcessado("abc"); registrarSantoAcessado(-1); registrarSantoAcessado(1.5);
    expect(listarSantosAcessados()).toEqual([]);
    localStorage.setItem(`${Prefixo_Das_Chaves}santos-acessados`, "{não é json");
    expect(listarSantosAcessados()).toEqual([]);
    localStorage.setItem(`${Prefixo_Das_Chaves}santos-acessados`, JSON.stringify([3, "4", 0, null, 3]));
    expect(listarSantosAcessados()).toEqual([3, 4]);
  });
});

describe("novena pessoal", () => {
  it("normaliza dias fora de 1..9 e tipos errados", () => {
    gravarJsonNoDispositivo("novena:1", { marcados: [3, 3, 0, 12, "2", 1], pedidos: 42 });
    expect(lerNovenaPessoal(1)).toEqual({ marcados: [1, 3], pedidos: "" });
  });
  it("alterna marcação e persiste só no dispositivo", () => {
    const dadosComDiaMarcado = alternarDiaMarcado({ marcados: [], pedidos: "" }, 4);
    expect(salvarNovenaPessoal(7, dadosComDiaMarcado).gravou).toBe(true);
    expect(lerNovenaPessoal(7).marcados).toEqual([4]);
    expect(alternarDiaMarcado(lerNovenaPessoal(7), 4).marcados).toEqual([]);
  });
  it("sem conteúdo remove a chave", () => {
    salvarNovenaPessoal(8, { marcados: [1], pedidos: "x" });
    salvarNovenaPessoal(8, { marcados: [], pedidos: "" });
    expect(localStorage.getItem(`${Prefixo_Das_Chaves}novena:8`)).toBeNull();
  });
  it("armazenamento indisponível não quebra", () => {
    const setItemOriginal = Storage.prototype.setItem;
    Storage.prototype.setItem = () => { throw new Error("QuotaExceededError"); };
    try {
      expect(gravarJsonNoDispositivo("x", 1)).toBe(false);
      expect(lerJsonDoDispositivo("x", "padrão")).toBe("padrão");
      expect(salvarNovenaPessoal(9, { marcados: [1], pedidos: "" }).gravou).toBe(false);
    } finally { Storage.prototype.setItem = setItemOriginal; }
  });
});

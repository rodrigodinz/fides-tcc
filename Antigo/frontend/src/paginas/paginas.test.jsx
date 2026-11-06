import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import App from "../App.jsx";
import { instalarFetch, paginaDe, respostaJson } from "../testes/fetchFalso.js";

const renderizar = (rota) => render(<MemoryRouter initialEntries={[rota]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><App /></MemoryRouter>);
const intervalo = { hoje: "2026-11-05", inicio: "2026-10-29", fim: "2026-11-12" };

beforeEach(() => { localStorage.clear(); window.scrollTo = vi.fn(); });

describe("Santos", () => {
  it("lista vazia mostra estado vazio, não erro", async () => {
    instalarFetch([["/santos", paginaDe([])]]);
    renderizar("/santos?q=francisco");
    expect(await screen.findByText("Nenhum santo encontrado para “francisco”")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("falha de rede mostra mensagem amigável e tenta de novo", async () => {
    let falhar = true;
    instalarFetch([["/santos", () => (falhar ? Promise.reject(new TypeError("Failed to fetch")) : respostaJson(paginaDe([{ id: 1, nome: "São Tomás de Aquino", foto_url: null }])))]]);
    renderizar("/santos");
    expect(await screen.findByText("Não foi possível carregar os santos no momento.")).toBeInTheDocument();
    falhar = false;
    await userEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(await screen.findByRole("link", { name: "São Tomás de Aquino" })).toHaveAttribute("href", "/santos/1");
    // sem foto_url: retrato substituto, sem imagem inventada
    expect(screen.getByText("Retrato não disponível")).toBeInTheDocument();
  });
});

describe("Santo", () => {
  it("registra o acesso no dispositivo e não mistura ids", async () => {
    const chamadas = instalarFetch([
      ["/santos/5", { id: 5, nome: "Santa Teresa d'Ávila", foto_url: null, biografia: "Carmelita.", oracoes: [], novenas: [], livros: [{ id: 1, titulo: "O Castelo Interior", autor: "Santa Teresa de Jesus" }] }],
    ]);
    renderizar("/santos/5");
    expect(await screen.findByRole("heading", { level: 1, name: "Santa Teresa d'Ávila" })).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("fides:v1:santos-acessados"))).toEqual([5]);
    expect(screen.getByRole("link", { name: "O Castelo Interior" })).toHaveAttribute("href", "/livros/1");
    expect(chamadas.some((u) => u.includes("/oracoes"))).toBe(false); // sem orações vinculadas, não consulta
  });

  it("santo inexistente mostra página de não encontrado", async () => {
    instalarFetch([["/santos/999", () => respostaJson({ erro: { codigo: "RECURSO_NAO_ENCONTRADO", mensagem: "x", detalhes: [] } }, 404)]]);
    renderizar("/santos/999");
    expect(await screen.findByText("Santo não encontrado")).toBeInTheDocument();
  });
});

describe("Novena", () => {
  const dias = Array.from({ length: 9 }, (_, i) => ({ id: i + 1, numero_dia: i + 1, data: null }));
  it("sem agenda: não inventa data nem 'Hoje'; marcação local não muda a agenda", async () => {
    instalarFetch([
      ["/novenas/3/dias/1", { novena: { id: 3, titulo: "Novena X" }, numero_dia: 1, total_dias: 9, data: null, dia_atual: null, texto_reflexao: "Reflexão um.", oracoes: [], dia_anterior: null, proximo_dia: 2 }],
      ["/novenas/3/dias", { novena: { id: 3, titulo: "Novena X" }, total_dias: 9, agenda: null, dias }],
      ["/novenas/3", { id: 3, titulo: "Novena X", descricao: null, santo: null, total_dias: 9, agenda: null }],
    ]);
    renderizar("/novenas/3");
    expect(await screen.findByText("Reflexão um.")).toBeInTheDocument();
    expect(screen.getAllByText("Não agendada").length).toBeGreaterThan(0);
    expect(screen.queryByText("Hoje")).not.toBeInTheDocument();
    await userEvent.click(screen.getByLabelText("Rezei o dia 1"));
    expect(JSON.parse(localStorage.getItem("fides:v1:novena:3")).marcados).toEqual([1]);
    const cal = screen.getByRole("list", { name: "Os nove dias da novena" });
    expect(within(cal).getByRole("link", { name: /Dia 1, marcado como rezado neste dispositivo/ })).toBeInTheDocument();
    expect(screen.getAllByText("Não agendada").length).toBeGreaterThan(0);
  });
});

describe("Livros", () => {
  it("sem santos acessados não chama /livros/recomendados", async () => {
    const chamadas = instalarFetch([["/santos", paginaDe([])], ["/livros", paginaDe([{ id: 6, titulo: "Teologia do Corpo", autor: "São João Paulo II", santo: null }])]]);
    renderizar("/livros");
    expect(await screen.findByRole("link", { name: "Teologia do Corpo" })).toBeInTheDocument();
    expect(screen.getByText("Ainda sem recomendações")).toBeInTheDocument();
    expect(chamadas.some((u) => u.includes("recomendados"))).toBe(false);
  });
  it("com santos acessados envia santo_id repetido", async () => {
    localStorage.setItem("fides:v1:santos-acessados", JSON.stringify([2, 5]));
    const chamadas = instalarFetch([["/santos", paginaDe([])], ["/livros/recomendados", paginaDe([{ id: 4, titulo: "História de uma Alma", autor: "Santa Teresinha", santo: { id: 2, nome: "Santa Teresinha" } }])], ["/livros", paginaDe([])]]);
    renderizar("/livros");
    expect(await screen.findByRole("link", { name: "História de uma Alma" })).toBeInTheDocument();
    expect(chamadas.find((u) => u.includes("recomendados"))).toMatch(/santo_id=2&santo_id=5/);
  });
});

describe("Liturgia", () => {
  it("data fora da janela mostra aviso e caminho de volta", async () => {
    instalarFetch([["/liturgia/dia", () => respostaJson({ erro: { codigo: "DATA_FORA_DO_INTERVALO", mensagem: "x", detalhes: [] } }, 400)]]);
    renderizar("/liturgia?data=2026-12-30");
    expect(await screen.findByText("Data fora do período disponível.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ir para hoje" })).toBeInTheDocument();
  });
  it("mostra o aviso da API e a Segunda Leitura só quando preenchida", async () => {
    instalarFetch([["/liturgia/dia", { data: "2026-11-05", intervalo, aviso: "Conteúdo de demonstração.", santo_celebrado: null, primeira_leitura: "L1", salmo: "S", evangelho: "E", segunda_leitura: null, possui_segunda_leitura: false }]]);
    renderizar("/liturgia");
    expect(await screen.findByText("Conteúdo de demonstração.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Primeira Leitura" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Segunda Leitura" })).not.toBeInTheDocument();
  });
});

describe("Orações", () => {
  it("cards de oração não têm imagens e filtros usam momento_id", async () => {
    const chamadas = instalarFetch([
      ["/momentos", [{ id: 4, codigo: "antes_de_dormir", nome: "Antes de dormir" }]],
      ["/santos", paginaDe([])],
      ["/oracoes", paginaDe([{ id: 1, titulo: "Pai Nosso", texto: "Pai nosso...", basica: true, santo: null, momentos: [] }])],
    ]);
    const { container } = renderizar("/oracoes");
    expect(await screen.findByRole("heading", { name: "Pai Nosso" })).toBeInTheDocument();
    expect(container.querySelector(".fd-oracao img")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Antes de dormir" }));
    await screen.findByRole("button", { name: "Antes de dormir", pressed: true });
    expect(chamadas.some((u) => u.includes("/oracoes?") && u.includes("momento_id=4"))).toBe(true);
  });
});

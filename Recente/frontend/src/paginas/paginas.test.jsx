import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import App from "../App.jsx";
import { instalarFetchFalso, montarPaginaDe, montarRespostaJson } from "../testes/fetchFalso.js";

const renderizarRota = (rota) => render(
  <MemoryRouter initialEntries={[rota]} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}><App /></MemoryRouter>,
);
const periodoDeTeste = { hoje: "2026-11-05", inicio: "2026-10-29", fim: "2026-11-12" };

beforeEach(() => { localStorage.clear(); window.scrollTo = vi.fn(); });

describe("Santos", () => {
  it("lista vazia mostra estado vazio, não erro", async () => {
    instalarFetchFalso([["/santos", montarPaginaDe([])]]);
    renderizarRota("/santos?nome=francisco");
    expect(await screen.findByText("Nenhum santo encontrado para “francisco”")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("falha de rede mostra mensagem amigável e tenta de novo", async () => {
    let deveFalhar = true;
    instalarFetchFalso([["/santos", () => (deveFalhar
      ? Promise.reject(new TypeError("Failed to fetch"))
      : montarRespostaJson(montarPaginaDe([{ id: 1, nome: "São Tomás de Aquino", foto_url: null }])))]]);
    renderizarRota("/santos");
    expect(await screen.findByText("Não foi possível carregar os santos no momento.")).toBeInTheDocument();
    deveFalhar = false;
    await userEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(await screen.findByRole("link", { name: "São Tomás de Aquino" })).toHaveAttribute("href", "/santos/1");
    expect(screen.getByText("Retrato não disponível")).toBeInTheDocument();
  });
});

describe("Santo", () => {
  it("registra o acesso no dispositivo e não mistura ids", async () => {
    const urlsChamadas = instalarFetchFalso([
      ["/santos/5", { id: 5, nome: "Santa Teresa d'Ávila", foto_url: null, biografia: "Carmelita.", oracoes: [], novenas: [], livros: [{ id: 1, titulo: "O Castelo Interior", autor: "Santa Teresa de Jesus" }] }],
    ]);
    renderizarRota("/santos/5");
    expect(await screen.findByRole("heading", { level: 1, name: "Santa Teresa d'Ávila" })).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem("fides:v1:santos-acessados"))).toEqual([5]);
    expect(screen.getByRole("link", { name: "O Castelo Interior" })).toHaveAttribute("href", "/livros/1");
    expect(urlsChamadas.some((url) => url.includes("/oracoes"))).toBe(false);
  });

  it("santo inexistente mostra página de não encontrado", async () => {
    instalarFetchFalso([["/santos/999", () => montarRespostaJson({ erro: { codigo: "RECURSO_NAO_ENCONTRADO", mensagem: "x", detalhes: [] } }, 404)]]);
    renderizarRota("/santos/999");
    expect(await screen.findByText("Santo não encontrado")).toBeInTheDocument();
  });
});

describe("Novena", () => {
  const diasDaNovena = Array.from({ length: 9 }, (_, posicao) => ({ id: posicao + 1, numero_do_dia: posicao + 1, data: null }));
  it("sem agenda: não inventa data nem 'Hoje'; marcação local não muda a agenda", async () => {
    instalarFetchFalso([
      ["/novenas/3/dias/1", { novena: { id: 3, titulo: "Novena X" }, numero_do_dia: 1, total_dias: 9, data: null, dia_atual: null, texto_reflexao: "Reflexão um.", oracoes: [], dia_anterior: null, proximo_dia: 2 }],
      ["/novenas/3/dias", { novena: { id: 3, titulo: "Novena X" }, total_dias: 9, agenda: null, dias: diasDaNovena }],
      ["/novenas/3", { id: 3, titulo: "Novena X", descricao: null, santo: null, total_dias: 9, agenda: null }],
    ]);
    renderizarRota("/novenas/3");
    expect(await screen.findByText("Reflexão um.")).toBeInTheDocument();
    expect(screen.getAllByText("Não agendada").length).toBeGreaterThan(0);
    expect(screen.queryByText("Hoje")).not.toBeInTheDocument();
    await userEvent.click(screen.getByLabelText("Rezei o dia 1"));
    expect(JSON.parse(localStorage.getItem("fides:v1:novena:3")).marcados).toEqual([1]);
    const calendario = screen.getByRole("list", { name: "Os nove dias da novena" });
    expect(within(calendario).getByRole("link", { name: /Dia 1, marcado como rezado neste dispositivo/ })).toBeInTheDocument();
    expect(screen.getAllByText("Não agendada").length).toBeGreaterThan(0);
  });
});

describe("Livros", () => {
  it("sem santos acessados não chama /livros/recomendados", async () => {
    const urlsChamadas = instalarFetchFalso([["/santos", montarPaginaDe([])], ["/livros", montarPaginaDe([{ id: 6, titulo: "Teologia do Corpo", autor: "São João Paulo II", santo: null }])]]);
    renderizarRota("/livros");
    expect(await screen.findByRole("link", { name: "Teologia do Corpo" })).toBeInTheDocument();
    expect(screen.getByText("Ainda sem recomendações")).toBeInTheDocument();
    expect(urlsChamadas.some((url) => url.includes("recomendados"))).toBe(false);
  });
  it("com santos acessados envia santo_id repetido", async () => {
    localStorage.setItem("fides:v1:santos-acessados", JSON.stringify([2, 5]));
    const urlsChamadas = instalarFetchFalso([
      ["/santos", montarPaginaDe([])],
      ["/livros/recomendados", montarPaginaDe([{ id: 4, titulo: "História de uma Alma", autor: "Santa Teresinha", santo: { id: 2, nome: "Santa Teresinha" } }])],
      ["/livros", montarPaginaDe([])],
    ]);
    renderizarRota("/livros");
    expect(await screen.findByRole("link", { name: "História de uma Alma" })).toBeInTheDocument();
    expect(urlsChamadas.find((url) => url.includes("recomendados"))).toMatch(/santo_id=2&santo_id=5/);
  });
});

describe("Liturgia", () => {
  it("data fora do período mostra aviso e caminho de volta", async () => {
    instalarFetchFalso([["/liturgia/dia", () => montarRespostaJson({ erro: { codigo: "DATA_FORA_DO_INTERVALO", mensagem: "x", detalhes: [] } }, 400)]]);
    renderizarRota("/liturgia?data=2026-12-30");
    expect(await screen.findByText("Data fora do período disponível.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ir para hoje" })).toBeInTheDocument();
  });
  it("mostra o aviso da API e a Segunda Leitura só quando preenchida", async () => {
    instalarFetchFalso([["/liturgia/dia", {
      data: "2026-11-05", periodo: periodoDeTeste, aviso: "Conteúdo de demonstração.", santo_celebrado: null,
      primeira_leitura: "L1", salmo: "S", evangelho: "E", segunda_leitura: null, tem_segunda_leitura_no_dia: false,
    }]]);
    renderizarRota("/liturgia");
    expect(await screen.findByText("Conteúdo de demonstração.")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Primeira Leitura" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Segunda Leitura" })).not.toBeInTheDocument();
  });
});

describe("Orações", () => {
  it("cards de oração não têm imagens e filtros usam momento_id", async () => {
    const urlsChamadas = instalarFetchFalso([
      ["/momentos", [{ id: 4, codigo: "antes_de_dormir", nome: "Antes de dormir" }]],
      ["/santos", montarPaginaDe([])],
      ["/oracoes", montarPaginaDe([{ id: 1, titulo: "Pai Nosso", texto: "Pai nosso...", basica: true, santo: null, momentos: [] }])],
    ]);
    const { container } = renderizarRota("/oracoes");
    expect(await screen.findByRole("heading", { name: "Pai Nosso" })).toBeInTheDocument();
    expect(container.querySelector(".fd-oracao img")).toBeNull();
    await userEvent.click(screen.getByRole("button", { name: "Antes de dormir" }));
    await screen.findByRole("button", { name: "Antes de dormir", pressed: true });
    expect(urlsChamadas.some((url) => url.includes("/oracoes?") && url.includes("momento_id=4"))).toBe(true);
  });
});

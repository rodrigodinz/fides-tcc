import { calcularPaginasVisiveis, lerNumeroDaPagina, lerIdDaUrl } from "./paginacao.js";
import { escreverDataCurta, escreverDataPorExtenso, ehDataIso, somarDias, dataDentroDoPeriodo } from "./datas.js";
import { descreverAgendaDaNovena, escolherDiaInicial } from "./novena.js";
import { ordenarHorasDaLiturgia } from "./liturgia.js";

describe("paginação", () => {
  it("atual ±2, só páginas que existem", () => {
    expect(calcularPaginasVisiveis(1, 9)).toEqual([1, 2, 3]);
    expect(calcularPaginasVisiveis(5, 9)).toEqual([3, 4, 5, 6, 7]);
    expect(calcularPaginasVisiveis(9, 9)).toEqual([7, 8, 9]);
    expect(calcularPaginasVisiveis(1, 0)).toEqual([]);
  });
  it("lê página e id com segurança", () => {
    expect(lerNumeroDaPagina("abc")).toBe(1); expect(lerNumeroDaPagina("0")).toBe(1); expect(lerNumeroDaPagina("3")).toBe(3);
    expect(lerIdDaUrl("2")).toBe(2); expect(lerIdDaUrl("x")).toBeNull(); expect(lerIdDaUrl("1.5")).toBeNull();
  });
});

describe("datas", () => {
  it("valida ISO e soma dias sem fuso", () => {
    expect(ehDataIso("2026-11-05")).toBe(true);
    expect(ehDataIso("2026-02-30")).toBe(false);
    expect(somarDias("2026-11-30", 1)).toBe("2026-12-01");
    expect(escreverDataCurta("2026-11-05")).toBe("05/11");
    expect(escreverDataPorExtenso("2026-11-05")).toMatch(/^Quinta-feira, 5 de novembro de 2026$/);
  });
  it("respeita o período da API", () => {
    const periodo = { hoje: "2026-11-05", inicio: "2026-10-29", fim: "2026-11-12" };
    expect(dataDentroDoPeriodo("2026-11-12", periodo)).toBe(true);
    expect(dataDentroDoPeriodo("2026-11-13", periodo)).toBe(false);
  });
});

describe("agenda da novena", () => {
  it("em andamento mostra Dia X de 9", () => {
    expect(descreverAgendaDaNovena({ situacao: "em_andamento", dia_atual: 5, data_inicio: "2026-11-01" }, 9).texto).toBe("Dia 5 de 9");
  });
  it("agendada com dia_atual 0 nunca mostra 'Dia 0'", () => {
    const situacao = descreverAgendaDaNovena({ situacao: "agendada", dia_atual: 0, data_inicio: "2026-11-07" }, 9);
    expect(situacao.tipo).toBe("agendada");
    expect(situacao.texto).not.toMatch(/Dia 0/);
    expect(situacao.texto).toMatch(/7 de novembro/);
  });
  it("agenda null é não agendada", () => {
    expect(descreverAgendaDaNovena(null).tipo).toBe("sem_agenda");
    expect(escolherDiaInicial(null)).toBe(1);
    expect(escolherDiaInicial({ situacao: "em_andamento", dia_atual: 4 })).toBe(4);
    expect(escolherDiaInicial({ situacao: "agendada", dia_atual: 0 })).toBe(1);
  });
});

it("ordena a Liturgia das Horas em ordem canônica", () => {
  const horasForaDeOrdem = [{ bloco: { codigo: "vesperas" } }, { bloco: { codigo: "laudes" } }, { bloco: { codigo: "horas_medias" } }];
  expect(ordenarHorasDaLiturgia(horasForaDeOrdem).map((hora) => hora.bloco.codigo)).toEqual(["laudes", "horas_medias", "vesperas"]);
});

import { paginasVisiveis, lerPagina, lerId } from "./paginacao.js";
import { dataCurta, dataPorExtenso, ehDataIso, somarDias, dentroDoIntervalo } from "./datas.js";
import { descreverAgenda, diaInicial } from "./novena.js";
import { ordenarHoras } from "./liturgia.js";

describe("paginação", () => {
  it("atual ±2, só páginas que existem", () => {
    expect(paginasVisiveis(1, 9)).toEqual([1, 2, 3]);
    expect(paginasVisiveis(5, 9)).toEqual([3, 4, 5, 6, 7]);
    expect(paginasVisiveis(9, 9)).toEqual([7, 8, 9]);
    expect(paginasVisiveis(1, 0)).toEqual([]);
  });
  it("lê página e id com segurança", () => {
    expect(lerPagina("abc")).toBe(1); expect(lerPagina("0")).toBe(1); expect(lerPagina("3")).toBe(3);
    expect(lerId("2")).toBe(2); expect(lerId("x")).toBeNull(); expect(lerId("1.5")).toBeNull();
  });
});

describe("datas", () => {
  it("valida ISO e soma dias sem fuso", () => {
    expect(ehDataIso("2026-11-05")).toBe(true);
    expect(ehDataIso("2026-02-30")).toBe(false);
    expect(somarDias("2026-11-30", 1)).toBe("2026-12-01");
    expect(dataCurta("2026-11-05")).toBe("05/11");
    expect(dataPorExtenso("2026-11-05")).toMatch(/^Quinta-feira, 5 de novembro de 2026$/);
  });
  it("respeita a janela da API", () => {
    const i = { hoje: "2026-11-05", inicio: "2026-10-29", fim: "2026-11-12" };
    expect(dentroDoIntervalo("2026-11-12", i)).toBe(true);
    expect(dentroDoIntervalo("2026-11-13", i)).toBe(false);
  });
});

describe("agenda da novena", () => {
  it("em andamento mostra Dia X de 9", () => {
    expect(descreverAgenda({ situacao: "em_andamento", dia_atual: 5, data_inicio: "2026-11-01" }, 9).texto).toBe("Dia 5 de 9");
  });
  it("agendada com dia_atual 0 nunca mostra 'Dia 0'", () => {
    const s = descreverAgenda({ situacao: "agendada", dia_atual: 0, data_inicio: "2026-11-07" }, 9);
    expect(s.tipo).toBe("agendada");
    expect(s.texto).not.toMatch(/Dia 0/);
    expect(s.texto).toMatch(/7 de novembro/);
  });
  it("agenda null é não agendada", () => {
    expect(descreverAgenda(null).tipo).toBe("sem_agenda");
    expect(diaInicial(null)).toBe(1);
    expect(diaInicial({ situacao: "em_andamento", dia_atual: 4 })).toBe(4);
    expect(diaInicial({ situacao: "agendada", dia_atual: 0 })).toBe(1);
  });
});

it("ordena a Liturgia das Horas em ordem canônica", () => {
  const h = [{ bloco: { codigo: "vesperas" } }, { bloco: { codigo: "laudes" } }, { bloco: { codigo: "horas_medias" } }];
  expect(ordenarHoras(h).map((x) => x.bloco.codigo)).toEqual(["laudes", "horas_medias", "vesperas"]);
});

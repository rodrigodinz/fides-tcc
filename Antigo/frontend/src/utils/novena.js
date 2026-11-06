/**
 * Situação da novena segundo a Agenda global da API (igual para todos os fiéis).
 * agenda = null → não agendada; situacao "agendada" com dia_atual 0 → ainda não começou.
 */
import { dataPorExtenso } from "./datas.js";

export function descreverAgenda(agenda, totalDias = 9) {
  if (!agenda) {
    return { tipo: "sem_agenda", rotulo: "Não agendada", texto: "Esta novena não tem agenda ativa no momento.", diaAtual: null };
  }
  if (agenda.situacao === "em_andamento" && agenda.dia_atual >= 1) {
    return { tipo: "em_andamento", rotulo: "Em andamento", texto: `Dia ${agenda.dia_atual} de ${totalDias}`, diaAtual: agenda.dia_atual };
  }
  return {
    tipo: "agendada",
    rotulo: "Agendada",
    texto: `Começa em ${dataPorExtenso(agenda.data_inicio, { semana: false })}`,
    diaAtual: null,
  };
}

/** Dia a abrir por padrão: o dia atual da agenda, se houver; senão o dia 1. */
export function diaInicial(agenda, totalDias = 9) {
  const d = agenda?.situacao === "em_andamento" ? agenda.dia_atual : 0;
  return d >= 1 && d <= totalDias ? d : 1;
}

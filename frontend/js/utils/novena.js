import { escreverDataPorExtenso } from "./datas.js";

// texto da situação da novena: em andamento (Dia X de 9), agendada (começa em...) ou não agendada
export function descreverAgendaDaNovena(agenda, totalDias = 9) {
  if (!agenda) {
    return { tipo: "sem_agenda", rotulo: "Não agendada", texto: "Esta novena não tem agenda ativa no momento.", diaAtual: null };
  }
  if (agenda.situacao === "em_andamento" && agenda.dia_atual >= 1) {
    return { tipo: "em_andamento", rotulo: "Em andamento", texto: `Dia ${agenda.dia_atual} de ${totalDias}`, diaAtual: agenda.dia_atual };
  }
  return {
    tipo: "agendada",
    rotulo: "Agendada",
    texto: `Começa em ${escreverDataPorExtenso(agenda.data_inicio, { comDiaDaSemana: false })}`,
    diaAtual: null,
  };
}

// abre a novena no dia atual da agenda; sem agenda, abre no dia 1
export function escolherDiaInicial(agenda, totalDias = 9) {
  const diaAtualDaAgenda = agenda?.situacao === "em_andamento" ? agenda.dia_atual : 0;
  return diaAtualDaAgenda >= 1 && diaAtualDaAgenda <= totalDias ? diaAtualDaAgenda : 1;
}

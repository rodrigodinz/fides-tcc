// guarda o último período da liturgia recebido, para o seletor de data aparecer mesmo quando dá erro
let ultimoPeriodoConhecido = null;

export const lembrarPeriodo = (periodo) => {
  if (periodo?.inicio && periodo?.fim) ultimoPeriodoConhecido = periodo;
};

export const periodoConhecido = () => ultimoPeriodoConhecido;

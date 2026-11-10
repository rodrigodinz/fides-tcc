/** Guarda em memória o último intervalo de datas informado pela API (hoje ± 7 dias),
 * para manter o seletor de data utilizável mesmo quando uma data devolve erro. */
let ultimo = null;
export const lembrarIntervalo = (intervalo) => { if (intervalo?.inicio && intervalo?.fim) ultimo = intervalo; };
export const intervaloConhecido = () => ultimo;

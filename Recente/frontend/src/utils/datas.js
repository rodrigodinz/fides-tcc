const Formato_Data_Iso = /^(\d{4})-(\d{2})-(\d{2})$/;

// confere se o texto é uma data real no formato AAAA-MM-DD
export function ehDataIso(texto) {
  const partesDaData = typeof texto === "string" && Formato_Data_Iso.exec(texto);
  if (!partesDaData) return false;
  const [, ano, mes, dia] = partesDaData.map(Number);
  const data = new Date(ano, mes - 1, dia);
  return data.getFullYear() === ano && data.getMonth() === mes - 1 && data.getDate() === dia;
}

// cria a data no fuso local (new Date("2026-11-05") usaria UTC e poderia voltar um dia)
export function converterIsoParaData(dataIso) {
  const [ano, mes, dia] = dataIso.split("-").map(Number);
  return new Date(ano, mes - 1, dia);
}

export function converterDataParaIso(data) {
  const completarComZero = (numero) => String(numero).padStart(2, "0");
  return `${data.getFullYear()}-${completarComZero(data.getMonth() + 1)}-${completarComZero(data.getDate())}`;
}

export function somarDias(dataIso, quantidadeDeDias) {
  const data = converterIsoParaData(dataIso);
  data.setDate(data.getDate() + quantidadeDeDias);
  return converterDataParaIso(data);
}

const colocarPrimeiraLetraMaiuscula = (texto) => texto.charAt(0).toUpperCase() + texto.slice(1);

export function escreverDataPorExtenso(dataIso, { comDiaDaSemana = true, comAno = true } = {}) {
  if (!ehDataIso(dataIso)) return "";
  const formatoDaData = { weekday: comDiaDaSemana ? "long" : undefined, day: "numeric", month: "long", year: comAno ? "numeric" : undefined };
  const dataPorExtenso = new Intl.DateTimeFormat("pt-BR", formatoDaData).format(converterIsoParaData(dataIso));
  return colocarPrimeiraLetraMaiuscula(dataPorExtenso);
}

export function escreverDataCurta(dataIso) {
  if (!ehDataIso(dataIso)) return "";
  const [, mes, dia] = dataIso.split("-");
  return `${dia}/${mes}`;
}

// verifica se a data está dentro do período que a API informou
export function dataDentroDoPeriodo(dataIso, periodo) {
  return Boolean(periodo) && ehDataIso(dataIso) && dataIso >= periodo.inicio && dataIso <= periodo.fim;
}

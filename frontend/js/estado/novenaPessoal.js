import { gravarJsonNoDispositivo, lerJsonDoDispositivo, removerDoDispositivo } from "./armazenamento.js";

const montarChaveDaNovena = (novenaId) => `novena:${novenaId}`;
export const Limite_De_Caracteres_Dos_Pedidos = 4000;

const ordenarDias = (diaA, diaB) => diaA - diaB;

// limpa o que veio do navegador: só dias de 1 a 9, sem repetição, e pedidos com até 4000 caracteres
function normalizarDadosDaNovena(dadosGuardados, totalDias = 9) {
  const marcados = Array.isArray(dadosGuardados?.marcados)
    ? [...new Set(dadosGuardados.marcados.filter((dia) => Number.isInteger(dia) && dia >= 1 && dia <= totalDias))].sort(ordenarDias)
    : [];
  const pedidos = typeof dadosGuardados?.pedidos === "string" ? dadosGuardados.pedidos.slice(0, Limite_De_Caracteres_Dos_Pedidos) : "";
  return { marcados, pedidos };
}

export function lerNovenaPessoal(novenaId, totalDias = 9) {
  const dadosGuardados = lerJsonDoDispositivo(montarChaveDaNovena(novenaId), null, (valor) => valor && typeof valor === "object");
  return normalizarDadosDaNovena(dadosGuardados, totalDias);
}

export function salvarNovenaPessoal(novenaId, dados, totalDias = 9) {
  const dadosLimpos = normalizarDadosDaNovena(dados, totalDias);
  if (dadosLimpos.marcados.length === 0 && dadosLimpos.pedidos === "") {
    return { gravou: removerDoDispositivo(montarChaveDaNovena(novenaId)), dados: dadosLimpos };
  }
  const gravou = gravarJsonNoDispositivo(montarChaveDaNovena(novenaId), { ...dadosLimpos, atualizadoEm: new Date().toISOString() });
  return { gravou, dados: dadosLimpos };
}

export function alternarDiaMarcado(dados, numeroDoDia) {
  const diaJaMarcado = dados.marcados.includes(numeroDoDia);
  const marcados = diaJaMarcado
    ? dados.marcados.filter((dia) => dia !== numeroDoDia)
    : [...dados.marcados, numeroDoDia].sort(ordenarDias);
  return { ...dados, marcados };
}

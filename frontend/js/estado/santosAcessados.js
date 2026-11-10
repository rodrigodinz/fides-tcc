import { gravarJsonNoDispositivo, lerJsonDoDispositivo } from "./armazenamento.js";

export const Chave_Dos_Santos_Acessados = "santos-acessados";
export const Maximo_De_Santos_Acessados = 20;

const ehIdValido = (valor) => Number.isInteger(valor) && valor >= 1;

export function listarSantosAcessados() {
  const idsGuardados = lerJsonDoDispositivo(Chave_Dos_Santos_Acessados, [], Array.isArray);
  const idsJaVistos = new Set();
  const idsValidos = [];
  for (const valorGuardado of idsGuardados) {
    const santoId = typeof valorGuardado === "string" ? Number(valorGuardado) : valorGuardado;
    if (ehIdValido(santoId) && !idsJaVistos.has(santoId)) { idsJaVistos.add(santoId); idsValidos.push(santoId); }
    if (idsValidos.length >= Maximo_De_Santos_Acessados) break;
  }
  return idsValidos;
}

// guarda os últimos 20 santos visitados
export function registrarSantoAcessado(santoIdRecebido) {
  const santoId = Number(santoIdRecebido);
  if (!ehIdValido(santoId)) return listarSantosAcessados();
  const idsAtualizados = [santoId, ...listarSantosAcessados().filter((idAnterior) => idAnterior !== santoId)]
    .slice(0, Maximo_De_Santos_Acessados);
  gravarJsonNoDispositivo(Chave_Dos_Santos_Acessados, idsAtualizados);
  return idsAtualizados;
}

/**
 * Marcações pessoais ("rezei este dia") e pedidos de uma novena, só neste dispositivo.
 * NÃO têm relação com o "Dia X de 9", que vem da Agenda global da API.
 */
import { gravarJson, lerJson, remover } from "./armazenamento.js";

const chave = (novenaId) => `novena:${novenaId}`;
export const LIMITE_PEDIDOS = 4000;

function normalizar(valor, totalDias = 9) {
  const marcados = Array.isArray(valor?.marcados)
    ? [...new Set(valor.marcados.filter((d) => Number.isInteger(d) && d >= 1 && d <= totalDias))].sort((a, b) => a - b)
    : [];
  const pedidos = typeof valor?.pedidos === "string" ? valor.pedidos.slice(0, LIMITE_PEDIDOS) : "";
  return { marcados, pedidos };
}

export function lerNovenaPessoal(novenaId, totalDias = 9) {
  return normalizar(lerJson(chave(novenaId), null, (v) => v && typeof v === "object"), totalDias);
}

export function salvarNovenaPessoal(novenaId, dados, totalDias = 9) {
  const limpo = normalizar(dados, totalDias);
  if (limpo.marcados.length === 0 && limpo.pedidos === "") return { ok: remover(chave(novenaId)), dados: limpo };
  return { ok: gravarJson(chave(novenaId), { ...limpo, atualizadoEm: new Date().toISOString() }), dados: limpo };
}

export function alternarMarcado(dados, dia) {
  const tem = dados.marcados.includes(dia);
  return { ...dados, marcados: tem ? dados.marcados.filter((d) => d !== dia) : [...dados.marcados, dia].sort((a, b) => a - b) };
}

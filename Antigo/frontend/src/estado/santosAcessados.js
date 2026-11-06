/** Santos acessados neste dispositivo (base da recomendação de livros, US12/UC13). */
import { gravarJson, lerJson } from "./armazenamento.js";

export const CHAVE_SANTOS = "santos-acessados";
export const MAXIMO_SANTOS = 20; // igual ao limite da rota /livros/recomendados

const idValido = (v) => Number.isInteger(v) && v >= 1;

export function listarSantosAcessados() {
  const lista = lerJson(CHAVE_SANTOS, [], Array.isArray);
  const vistos = new Set();
  const limpos = [];
  for (const v of lista) {
    const n = typeof v === "string" ? Number(v) : v;
    if (idValido(n) && !vistos.has(n)) { vistos.add(n); limpos.push(n); }
    if (limpos.length >= MAXIMO_SANTOS) break;
  }
  return limpos;
}

/** Registra o acesso: deduplica, coloca o mais recente na frente e limita a 20. */
export function registrarSantoAcessado(id) {
  const n = Number(id);
  if (!idValido(n)) return listarSantosAcessados();
  const lista = [n, ...listarSantosAcessados().filter((x) => x !== n)].slice(0, MAXIMO_SANTOS);
  gravarJson(CHAVE_SANTOS, lista);
  return lista;
}

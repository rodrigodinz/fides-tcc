/**
 * Acesso seguro ao localStorage: tolera armazenamento indisponível (modo privado,
 * bloqueado), JSON inválido, dados de versões antigas e limite de espaço.
 * Tudo o que é pessoal fica só neste dispositivo; nada é enviado à API.
 */
export const PREFIXO = "fides:v1:";

function obterArmazenamento() {
  try {
    const s = globalThis.localStorage;
    if (!s) return null;
    const teste = `${PREFIXO}__teste__`;
    s.setItem(teste, "1");
    s.removeItem(teste);
    return s;
  } catch {
    return null;
  }
}

export function armazenamentoDisponivel() {
  return obterArmazenamento() !== null;
}

/** Lê e valida; devolve `padrao` se ausente, inválido ou se `validar` reprovar. */
export function lerJson(chave, padrao, validar = () => true) {
  const s = obterArmazenamento();
  if (!s) return padrao;
  try {
    const bruto = s.getItem(PREFIXO + chave);
    if (bruto === null) return padrao;
    const valor = JSON.parse(bruto);
    return validar(valor) ? valor : padrao;
  } catch {
    return padrao;
  }
}

/** Grava; devolve false se não for possível (indisponível ou cota excedida). */
export function gravarJson(chave, valor) {
  const s = obterArmazenamento();
  if (!s) return false;
  try {
    s.setItem(PREFIXO + chave, JSON.stringify(valor));
    return true;
  } catch {
    return false;
  }
}

export function remover(chave) {
  const s = obterArmazenamento();
  if (!s) return false;
  try {
    s.removeItem(PREFIXO + chave);
    return true;
  } catch {
    return false;
  }
}

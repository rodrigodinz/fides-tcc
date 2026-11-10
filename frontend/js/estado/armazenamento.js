export const Prefixo_Das_Chaves = "fides:v1:";

// localStorage pode estar bloqueado (aba anônima, cota cheia); esta verificação evita que o site quebre
function obterArmazenamentoLocal() {
  try {
    const armazenamentoLocal = globalThis.localStorage;
    if (!armazenamentoLocal) return null;
    const chaveDeVerificacao = `${Prefixo_Das_Chaves}__verificacao__`;
    armazenamentoLocal.setItem(chaveDeVerificacao, "1");
    armazenamentoLocal.removeItem(chaveDeVerificacao);
    return armazenamentoLocal;
  } catch {
    return null;
  }
}

export function armazenamentoDisponivel() {
  return obterArmazenamentoLocal() !== null;
}

// lê do localStorage; se o dado estiver corrompido devolve o valor padrão
export function lerJsonDoDispositivo(chave, valorPadrao, validarValor = () => true) {
  const armazenamentoLocal = obterArmazenamentoLocal();
  if (!armazenamentoLocal) return valorPadrao;
  try {
    const textoGuardado = armazenamentoLocal.getItem(Prefixo_Das_Chaves + chave);
    if (textoGuardado === null) return valorPadrao;
    const valorGuardado = JSON.parse(textoGuardado);
    return validarValor(valorGuardado) ? valorGuardado : valorPadrao;
  } catch {
    return valorPadrao;
  }
}

export function gravarJsonNoDispositivo(chave, valor) {
  const armazenamentoLocal = obterArmazenamentoLocal();
  if (!armazenamentoLocal) return false;
  try {
    armazenamentoLocal.setItem(Prefixo_Das_Chaves + chave, JSON.stringify(valor));
    return true;
  } catch {
    return false;
  }
}

export function removerDoDispositivo(chave) {
  const armazenamentoLocal = obterArmazenamentoLocal();
  if (!armazenamentoLocal) return false;
  try {
    armazenamentoLocal.removeItem(Prefixo_Das_Chaves + chave);
    return true;
  } catch {
    return false;
  }
}

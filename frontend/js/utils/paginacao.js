// botões da paginação: página atual e até 2 de cada lado
export function calcularPaginasVisiveis(paginaAtual, totalDePaginas) {
  if (!Number.isInteger(totalDePaginas) || totalDePaginas < 1) return [];
  const paginaAtualValida = Math.min(Math.max(1, paginaAtual), totalDePaginas);
  const paginasVisiveis = [];
  for (let numeroDaPagina = paginaAtualValida - 2; numeroDaPagina <= paginaAtualValida + 2; numeroDaPagina += 1) {
    if (numeroDaPagina >= 1 && numeroDaPagina <= totalDePaginas) paginasVisiveis.push(numeroDaPagina);
  }
  return paginasVisiveis;
}

export function lerNumeroDaPagina(valorDaUrl) {
  const numeroDaPagina = Number(valorDaUrl);
  return Number.isInteger(numeroDaPagina) && numeroDaPagina >= 1 ? numeroDaPagina : 1;
}

// converte o id da URL em número; texto inválido vira null (página de não encontrado)
export function lerIdDaUrl(valorDaUrl) {
  const id = Number(valorDaUrl);
  return Number.isInteger(id) && id >= 1 ? id : null;
}

// Leitura e escrita dos parâmetros da URL (?nome=...&pagina=2).
// Guardar filtros na URL permite voltar no navegador e compartilhar o link.
export function lerParametrosDaUrl() {
  return new URLSearchParams(window.location.search);
}

// altera os parâmetros sem recarregar a página; substituir=true não cria um passo novo no "voltar"
export function atualizarParametrosDaUrl(novosParametros, { substituir = false } = {}) {
  const textoDosParametros = novosParametros.toString();
  const novoEndereco = `${window.location.pathname}${textoDosParametros ? `?${textoDosParametros}` : ""}`;
  if (substituir) window.history.replaceState(null, "", novoEndereco);
  else window.history.pushState(null, "", novoEndereco);
}

// quando a pessoa usa o voltar/avançar do navegador, a página redesenha com os parâmetros novos
export function aoMudarParametrosDaUrl(funcao) {
  window.addEventListener("popstate", funcao);
}

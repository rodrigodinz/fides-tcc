// Todo texto que vem da API passa por aqui antes de entrar no HTML
export function escaparHtml(texto) {
  return String(texto ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

let contadorDeIds = 0;
// gera um id único na página
export function gerarId(prefixo) {
  contadorDeIds += 1;
  return `${prefixo}-${contadorDeIds}`;
}

export function criarElemento(textoHtml) {
  const modelo = document.createElement("template");
  modelo.innerHTML = textoHtml.trim();
  return modelo.content.firstElementChild;
}

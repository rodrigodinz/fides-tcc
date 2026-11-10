// Todo texto que vem da API passa por aqui antes de entrar no HTML.
// Isso impede que um texto com "<script>" vire código na página (proteção contra XSS).
export function escaparHtml(texto) {
  return String(texto ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

let contadorDeIds = 0;
// gera um id único na página (ex.: para ligar um <label> ao seu <input>)
export function gerarId(prefixo) {
  contadorDeIds += 1;
  return `${prefixo}-${contadorDeIds}`;
}

// transforma um texto de HTML em elementos de verdade e devolve o primeiro
export function criarElemento(textoHtml) {
  const modelo = document.createElement("template");
  modelo.innerHTML = textoHtml.trim();
  return modelo.content.firstElementChild;
}

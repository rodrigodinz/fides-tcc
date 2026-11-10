// Endereço de cada página do site. Detalhes usam parâmetros na URL: santo.html?id=5
export const enderecos = {
  inicio: () => "/",
  santos: () => "/santos.html",
  santo: (santoId) => `/santo.html?id=${santoId}`,
  oracoes: () => "/oracoes.html",
  novenas: () => "/novenas.html",
  novena: (novenaId, numeroDoDia) => `/novena.html?id=${novenaId}${numeroDoDia ? `&dia=${numeroDoDia}` : ""}`,
  livros: () => "/livros.html",
  livro: (livroId) => `/livro.html?id=${livroId}`,
  liturgiaDoDia: (data) => `/liturgia.html${data ? `?data=${data}` : ""}`,
  liturgiaDasHoras: (data) => `/liturgia-horas.html${data ? `?data=${data}` : ""}`,
  agenda: (data) => `/agenda.html${data ? `?data=${data}` : ""}`,
};

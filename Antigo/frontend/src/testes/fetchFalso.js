/** Mock de fetch SÓ para testes: responde por trecho de URL. Nunca usado pela aplicação. */
export function respostaJson(corpo, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(corpo), { status, headers: { "Content-Type": "application/json" } }));
}

export function instalarFetch(rotas) {
  const chamadas = [];
  const fn = vi.fn((url) => {
    chamadas.push(url);
    for (const [trecho, resposta] of rotas) {
      if (url.includes(trecho)) return typeof resposta === "function" ? resposta(url) : respostaJson(resposta);
    }
    return respostaJson({ erro: { codigo: "ROTA_NAO_ENCONTRADA", mensagem: "x", detalhes: [] } }, 404);
  });
  vi.stubGlobal("fetch", fn);
  return chamadas;
}

export const paginaDe = (itens) => ({ itens, pagina: 1, limite: 20, total: itens.length, total_paginas: itens.length ? 1 : 0 });

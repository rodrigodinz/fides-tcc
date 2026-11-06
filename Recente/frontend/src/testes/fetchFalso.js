export function montarRespostaJson(corpo, status = 200) {
  return Promise.resolve(new Response(JSON.stringify(corpo), { status, headers: { "Content-Type": "application/json" } }));
}

export function instalarFetchFalso(rotasFalsas) {
  const urlsChamadas = [];
  const fetchFalso = vi.fn((url) => {
    urlsChamadas.push(url);
    for (const [trechoDaUrl, respostaFalsa] of rotasFalsas) {
      if (url.includes(trechoDaUrl)) return typeof respostaFalsa === "function" ? respostaFalsa(url) : montarRespostaJson(respostaFalsa);
    }
    return montarRespostaJson({ erro: { codigo: "ROTA_NAO_ENCONTRADA", mensagem: "x", detalhes: [] } }, 404);
  });
  vi.stubGlobal("fetch", fetchFalso);
  return urlsChamadas;
}

export const montarPaginaDe = (itens) => ({ itens, pagina: 1, limite: 20, total_registros_filtros: itens.length, total_paginas: itens.length ? 1 : 0 });

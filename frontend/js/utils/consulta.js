import { ehCancelamentoDaConsulta } from "../api/cliente.js";

// Cria um "consultor" para uma área da página. Se uma busca nova começar antes da anterior
// terminar (ex.: a pessoa trocou o filtro), a anterior é cancelada e o resultado dela é ignorado.
// Devolve { estado: "sucesso" | "vazio" | "erro" | "cancelado", dados, erro }.
export function criarConsulta() {
  let controladorAtual = null;
  return async function consultar(funcaoDeBusca, { verificarSeVazio } = {}) {
    controladorAtual?.abort();
    const controladorDestaBusca = new AbortController();
    controladorAtual = controladorDestaBusca;
    try {
      const dados = await funcaoDeBusca(controladorDestaBusca.signal);
      if (controladorDestaBusca.signal.aborted) return { estado: "cancelado" };
      const resultadoVazio = verificarSeVazio ? verificarSeVazio(dados) : false;
      return { estado: resultadoVazio ? "vazio" : "sucesso", dados };
    } catch (erro) {
      if (controladorDestaBusca.signal.aborted || ehCancelamentoDaConsulta(erro)) return { estado: "cancelado" };
      return { estado: "erro", erro };
    }
  };
}

export const paginaEstaVazia = (pagina) => !pagina || !Array.isArray(pagina.itens) || pagina.itens.length === 0;

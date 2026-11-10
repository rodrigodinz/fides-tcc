import { useCallback, useEffect, useRef, useState } from "react";
import { ehCancelamentoDaConsulta } from "../api/cliente.js";

const Resultado_Inicial = { estado: "carregando", dados: null, erro: null };

// Hook (função do React que guarda estado) usado por todas as páginas para buscar dados.
// Devolve { estado, dados, erro, recarregar }, onde estado é carregando | sucesso | vazio | erro.
// chaveDaConsulta: quando ela muda (ex.: outra página, outro filtro), a busca é refeita.
export function useConsulta(chaveDaConsulta, funcaoDeBusca, { verificarSeVazio, consultaAtiva = true } = {}) {
  // useState: valor que, quando muda, faz o componente ser desenhado de novo
  const [resultado, setResultado] = useState({ ...Resultado_Inicial, chaveDaConsulta: null });
  const [numeroDaTentativa, setNumeroDaTentativa] = useState(0);
  const referenciaDaBusca = useRef(funcaoDeBusca);
  const referenciaDaVerificacaoDeVazio = useRef(verificarSeVazio);
  referenciaDaBusca.current = funcaoDeBusca;
  referenciaDaVerificacaoDeVazio.current = verificarSeVazio;

  // useEffect: roda depois de desenhar; aqui dispara a busca sempre que a chave muda
  useEffect(() => {
    if (!consultaAtiva) return undefined;
    const controladorDeCancelamento = new AbortController();
    setResultado({ ...Resultado_Inicial, chaveDaConsulta });
    Promise.resolve()
      .then(() => referenciaDaBusca.current(controladorDeCancelamento.signal))
      .then((dados) => {
        if (controladorDeCancelamento.signal.aborted) return;
        const resultadoVazio = referenciaDaVerificacaoDeVazio.current ? referenciaDaVerificacaoDeVazio.current(dados) : false;
        setResultado({ estado: resultadoVazio ? "vazio" : "sucesso", dados, erro: null, chaveDaConsulta });
      })
      .catch((erro) => {
        if (controladorDeCancelamento.signal.aborted || ehCancelamentoDaConsulta(erro)) return;
        setResultado({ estado: "erro", dados: null, erro, chaveDaConsulta });
      });
    // limpeza: se a chave mudar antes de terminar, cancela a busca antiga
    return () => controladorDeCancelamento.abort();
  }, [chaveDaConsulta, numeroDaTentativa, consultaAtiva]);

  // usado pelo botão "Tentar novamente"
  const recarregar = useCallback(() => setNumeroDaTentativa((tentativaAnterior) => tentativaAnterior + 1), []);
  const resultadoAtual = resultado.chaveDaConsulta === chaveDaConsulta ? resultado : { ...Resultado_Inicial };
  return { ...resultadoAtual, recarregar };
}

export const paginaEstaVazia = (pagina) => !pagina || !Array.isArray(pagina.itens) || pagina.itens.length === 0;

/**
 * Estado de uma consulta à API: carregando → sucesso | vazio | erro.
 * Ao mudar a `chave` (filtro, página, data, id) o resultado anterior é descartado
 * imediatamente e a requisição anterior é cancelada: nunca mostramos dados antigos
 * como se fossem da nova consulta.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { ehCancelamento } from "../api/cliente.js";

const INICIAL = { estado: "carregando", dados: null, erro: null };

export function useConsulta(chave, buscar, { vazio, ativo = true } = {}) {
  const [resultado, setResultado] = useState({ ...INICIAL, chave: null });
  const [tentativa, setTentativa] = useState(0);
  const buscarRef = useRef(buscar);
  const vazioRef = useRef(vazio);
  buscarRef.current = buscar;
  vazioRef.current = vazio;

  useEffect(() => {
    if (!ativo) return undefined;
    const controle = new AbortController();
    setResultado({ ...INICIAL, chave });
    Promise.resolve()
      .then(() => buscarRef.current(controle.signal))
      .then((dados) => {
        if (controle.signal.aborted) return;
        const ehVazio = vazioRef.current ? vazioRef.current(dados) : false;
        setResultado({ estado: ehVazio ? "vazio" : "sucesso", dados, erro: null, chave });
      })
      .catch((erro) => {
        if (controle.signal.aborted || ehCancelamento(erro)) return;
        setResultado({ estado: "erro", dados: null, erro, chave });
      });
    return () => controle.abort();
  }, [chave, tentativa, ativo]);

  const recarregar = useCallback(() => setTentativa((t) => t + 1), []);
  // Enquanto o efeito da nova chave não roda, trata como carregando (evita um quadro com dados velhos).
  const atual = resultado.chave === chave ? resultado : { ...INICIAL };
  return { ...atual, recarregar };
}

export const listaVazia = (pagina) => !pagina || !Array.isArray(pagina.itens) || pagina.itens.length === 0;

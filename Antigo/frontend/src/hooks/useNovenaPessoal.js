/** Estado pessoal de uma novena (marcações e pedidos), persistido só no dispositivo. */
import { useCallback, useEffect, useState } from "react";
import { armazenamentoDisponivel } from "../estado/armazenamento.js";
import { alternarMarcado, lerNovenaPessoal, salvarNovenaPessoal } from "../estado/novenaPessoal.js";

export function useNovenaPessoal(novenaId, totalDias = 9) {
  const [dados, setDados] = useState(() => lerNovenaPessoal(novenaId, totalDias));
  const [disponivel] = useState(() => armazenamentoDisponivel());
  const [falhouGravar, setFalhouGravar] = useState(false);

  useEffect(() => { setDados(lerNovenaPessoal(novenaId, totalDias)); }, [novenaId, totalDias]);

  const persistir = useCallback((novo) => {
    const { ok, dados: limpo } = salvarNovenaPessoal(novenaId, novo, totalDias);
    setDados(limpo);
    setFalhouGravar(!ok);
    return ok;
  }, [novenaId, totalDias]);

  const alternar = useCallback((dia) => persistir(alternarMarcado(dados, dia)), [dados, persistir]);
  const salvarPedidos = useCallback((texto) => persistir({ ...dados, pedidos: texto }), [dados, persistir]);
  const limparPedidos = useCallback(() => persistir({ ...dados, pedidos: "" }), [dados, persistir]);
  const limparMarcacoes = useCallback(() => persistir({ ...dados, marcados: [] }), [dados, persistir]);

  return { ...dados, disponivel, falhouGravar, alternar, salvarPedidos, limparPedidos, limparMarcacoes };
}

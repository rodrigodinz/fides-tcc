import { useCallback, useEffect, useState } from "react";
import { armazenamentoDisponivel } from "../estado/armazenamento.js";
import { alternarDiaMarcado, lerNovenaPessoal, salvarNovenaPessoal } from "../estado/novenaPessoal.js";

// Marcações ("rezei o dia X") e pedidos da novena, guardados só no navegador (localStorage).
// Não vão para a API e não mudam o dia da agenda, que é igual para todos.
export function useNovenaPessoal(novenaId, totalDias = 9) {
  const [dadosPessoais, setDadosPessoais] = useState(() => lerNovenaPessoal(novenaId, totalDias));
  const [armazenamentoEstaDisponivel] = useState(() => armazenamentoDisponivel());
  const [falhouAoGravar, setFalhouAoGravar] = useState(false);

  useEffect(() => { setDadosPessoais(lerNovenaPessoal(novenaId, totalDias)); }, [novenaId, totalDias]);

  const persistirNoDispositivo = useCallback((novosDados) => {
    const { gravou, dados: dadosLimpos } = salvarNovenaPessoal(novenaId, novosDados, totalDias);
    setDadosPessoais(dadosLimpos);
    setFalhouAoGravar(!gravou);
    return gravou;
  }, [novenaId, totalDias]);

  const alternarDiaRezado = useCallback((numeroDoDia) => persistirNoDispositivo(alternarDiaMarcado(dadosPessoais, numeroDoDia)), [dadosPessoais, persistirNoDispositivo]);
  const salvarPedidos = useCallback((textoDosPedidos) => persistirNoDispositivo({ ...dadosPessoais, pedidos: textoDosPedidos }), [dadosPessoais, persistirNoDispositivo]);
  const limparPedidos = useCallback(() => persistirNoDispositivo({ ...dadosPessoais, pedidos: "" }), [dadosPessoais, persistirNoDispositivo]);
  const limparMarcacoes = useCallback(() => persistirNoDispositivo({ ...dadosPessoais, marcados: [] }), [dadosPessoais, persistirNoDispositivo]);

  return {
    ...dadosPessoais,
    armazenamentoEstaDisponivel,
    falhouAoGravar,
    alternarDiaRezado,
    salvarPedidos,
    limparPedidos,
    limparMarcacoes,
  };
}

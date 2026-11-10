import { useEffect, useState } from "react";

/** Valor que só muda depois de `ms` sem alterações (busca enquanto digita). */
export function useAtraso(valor, ms = 350) {
  const [atrasado, setAtrasado] = useState(valor);
  useEffect(() => {
    const t = setTimeout(() => setAtrasado(valor), ms);
    return () => clearTimeout(t);
  }, [valor, ms]);
  return atrasado;
}

import { useEffect, useState } from "react";

// espera o usuário parar de digitar (350 ms) antes de usar o valor; evita uma busca por letra
export function useAtraso(valor, milissegundos = 350) {
  const [valorAtrasado, setValorAtrasado] = useState(valor);
  useEffect(() => {
    const temporizador = setTimeout(() => setValorAtrasado(valor), milissegundos);
    return () => clearTimeout(temporizador);
  }, [valor, milissegundos]);
  return valorAtrasado;
}

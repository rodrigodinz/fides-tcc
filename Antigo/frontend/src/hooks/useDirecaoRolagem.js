/**
 * Navbar: esconde ao rolar para baixo e reaparece ao rolar para cima.
 * Histerese de 24px acumulados no mesmo sentido evita tremidas; rAF evita trabalho por pixel.
 */
import { useEffect, useState } from "react";

export const HISTERESE = 24;
export const ZONA_TOPO = 16;

export function useDirecaoRolagem({ pausado = false } = {}) {
  const [escondida, setEscondida] = useState(false);

  useEffect(() => {
    if (pausado) { setEscondida(false); return undefined; }
    let ultimo = window.scrollY;
    let acumulado = 0;
    let agendado = false;
    const atualizar = () => {
      agendado = false;
      const y = window.scrollY;
      const delta = y - ultimo;
      ultimo = y;
      if (y <= ZONA_TOPO) { acumulado = 0; setEscondida(false); return; }
      if (delta === 0) return;
      acumulado = Math.sign(delta) === Math.sign(acumulado) ? acumulado + delta : delta;
      if (acumulado > HISTERESE) setEscondida(true);
      else if (acumulado < -HISTERESE) setEscondida(false);
    };
    const aoRolar = () => { if (!agendado) { agendado = true; requestAnimationFrame(atualizar); } };
    window.addEventListener("scroll", aoRolar, { passive: true });
    return () => window.removeEventListener("scroll", aoRolar);
  }, [pausado]);

  return escondida;
}

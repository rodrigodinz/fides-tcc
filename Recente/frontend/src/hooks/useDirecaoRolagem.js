import { useEffect, useState } from "react";

export const Distancia_Minima_De_Rolagem = 24;
export const Altura_Da_Zona_Do_Topo = 16;

// esconde a navbar quando a pessoa rola para baixo e mostra de novo ao rolar para cima
export function useDirecaoRolagem({ rolagemPausada = false } = {}) {
  const [navbarEscondida, setNavbarEscondida] = useState(false);

  useEffect(() => {
    if (rolagemPausada) { setNavbarEscondida(false); return undefined; }
    let ultimaPosicao = window.scrollY;
    let distanciaAcumulada = 0;
    let atualizacaoAgendada = false;
    const atualizarNavbar = () => {
      atualizacaoAgendada = false;
      const posicaoAtual = window.scrollY;
      const diferencaDePosicao = posicaoAtual - ultimaPosicao;
      ultimaPosicao = posicaoAtual;
      if (posicaoAtual <= Altura_Da_Zona_Do_Topo) { distanciaAcumulada = 0; setNavbarEscondida(false); return; }
      if (diferencaDePosicao === 0) return;
      distanciaAcumulada = Math.sign(diferencaDePosicao) === Math.sign(distanciaAcumulada)
        ? distanciaAcumulada + diferencaDePosicao
        : diferencaDePosicao;
      if (distanciaAcumulada > Distancia_Minima_De_Rolagem) setNavbarEscondida(true);
      else if (distanciaAcumulada < -Distancia_Minima_De_Rolagem) setNavbarEscondida(false);
    };
    const aoRolarAPagina = () => {
      if (!atualizacaoAgendada) { atualizacaoAgendada = true; requestAnimationFrame(atualizarNavbar); }
    };
    window.addEventListener("scroll", aoRolarAPagina, { passive: true });
    return () => window.removeEventListener("scroll", aoRolarAPagina);
  }, [rolagemPausada]);

  return navbarEscondida;
}

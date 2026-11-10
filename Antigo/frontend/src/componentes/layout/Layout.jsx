import { useCallback, useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Navbar from "./Navbar.jsx";
import Drawer from "./Drawer.jsx";
import Rodape from "./Rodape.jsx";

/** Estrutura global: pular para o conteúdo, navbar, drawer, conteúdo com trilhos laterais e rodapé. */
export default function Layout() {
  const [aberto, setAberto] = useState(false);
  const refMenu = useRef(null);
  const refPrincipal = useRef(null);
  const { pathname } = useLocation();
  const primeiraRota = useRef(true);

  const fechar = useCallback(() => {
    setAberto(false);
    setTimeout(() => refMenu.current?.focus(), 0);
  }, []);

  // Troca de rota: fecha o menu, volta ao topo e leva o foco ao conteúdo (leitores de tela).
  useEffect(() => {
    setAberto(false);
    if (primeiraRota.current) { primeiraRota.current = false; return; }
    window.scrollTo({ top: 0 });
    refPrincipal.current?.focus({ preventScroll: true });
  }, [pathname]);

  return (
    <div className="fd-app">
      <a href="#conteudo" className="fd-pular">Pular para o conteúdo</a>
      <Navbar ref={refMenu} drawerAberto={aberto} aoAbrirMenu={() => setAberto(true)} />
      <Drawer aberto={aberto} aoFechar={fechar} />
      <main id="conteudo" ref={refPrincipal} tabIndex={-1} className="fd-principal">
        <div className="fd-trilho fd-trilho--esq" aria-hidden="true" />
        <div className="fd-trilho fd-trilho--dir" aria-hidden="true" />
        <Outlet />
      </main>
      <Rodape />
    </div>
  );
}

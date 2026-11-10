import { useCallback, useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Navbar from "./Navbar.jsx";
import Drawer from "./Drawer.jsx";
import Rodape from "./Rodape.jsx";

// Moldura de todas as páginas: navbar, menu lateral, conteúdo e rodapé.
// <Outlet /> é o lugar onde a página da rota atual é desenhada.
export default function Layout() {
  const [menuAberto, setMenuAberto] = useState(false);
  const referenciaDoBotaoMenu = useRef(null);
  const referenciaDoConteudoPrincipal = useRef(null);
  const { pathname: caminhoAtual } = useLocation();
  const ehPrimeiraRota = useRef(true);

  const fecharMenu = useCallback(() => {
    setMenuAberto(false);
    setTimeout(() => referenciaDoBotaoMenu.current?.focus(), 0);
  }, []);

  // ao trocar de página: fecha o menu, volta ao topo e leva o foco para o conteúdo
  useEffect(() => {
    setMenuAberto(false);
    if (ehPrimeiraRota.current) { ehPrimeiraRota.current = false; return; }
    window.scrollTo({ top: 0 });
    referenciaDoConteudoPrincipal.current?.focus({ preventScroll: true });
  }, [caminhoAtual]);

  return (
    <div className="fd-app">
      <a href="#conteudo" className="fd-pular">Pular para o conteúdo</a>
      <Navbar ref={referenciaDoBotaoMenu} menuAberto={menuAberto} aoAbrirMenu={() => setMenuAberto(true)} />
      <Drawer aberto={menuAberto} aoFechar={fecharMenu} />
      <main id="conteudo" ref={referenciaDoConteudoPrincipal} tabIndex={-1} className="fd-principal">
        <div className="fd-trilho fd-trilho--esq" aria-hidden="true" />
        <div className="fd-trilho fd-trilho--dir" aria-hidden="true" />
        <Outlet />
      </main>
      <Rodape />
    </div>
  );
}

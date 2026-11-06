import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";
import { Modulos } from "../../navegacao.js";
import Icone from "../Icone.jsx";
import Ornamento from "../Ornamento.jsx";
import { prenderFocoNoContainer } from "../focoPreso.js";

// menu lateral; Esc fecha e trava a rolagem da página enquanto aberto
export default function Drawer({ aberto, aoFechar }) {
  const referenciaDoDrawer = useRef(null);
  const referenciaDoBotaoFechar = useRef(null);

  useEffect(() => {
    if (!aberto) return undefined;
    document.body.classList.add("fd-sem-rolagem");
    const temporizadorDoFoco = setTimeout(() => referenciaDoBotaoFechar.current?.focus(), 30);
    const aoPressionarTecla = (evento) => {
      if (evento.key === "Escape") { evento.preventDefault(); aoFechar(); }
      else prenderFocoNoContainer(evento, referenciaDoDrawer.current);
    };
    document.addEventListener("keydown", aoPressionarTecla);
    return () => {
      clearTimeout(temporizadorDoFoco);
      document.body.classList.remove("fd-sem-rolagem");
      document.removeEventListener("keydown", aoPressionarTecla);
    };
  }, [aberto, aoFechar]);

  return (
    <>
      <div className={`fd-veu${aberto ? " is-aberto" : ""}`} onClick={aoFechar} aria-hidden="true" />
      <aside id="fd-menu" ref={referenciaDoDrawer} className={`fd-drawer${aberto ? " is-aberto" : ""}`} role="dialog" aria-modal="true" aria-label="Menu" aria-hidden={!aberto}>
        <div className="fd-drawer__topo">
          <Ornamento tipo="curto" />
          <button ref={referenciaDoBotaoFechar} type="button" className="fd-botao-icone" aria-label="Fechar menu" onClick={aoFechar}>
            <Icone nome="fechar" />
          </button>
        </div>
        <nav className="fd-drawer__nav" aria-label="Módulos">
          <ul>
            {Modulos.map((modulo) => (
              <li key={modulo.rota}>
                <NavLink to={modulo.rota} end={modulo.rotaExata} onClick={aoFechar}><Icone nome={modulo.icone} tamanho={24} />{modulo.nome}</NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <div className="fd-drawer__inst">
          <h2>Sobre o Fides</h2>
          <p>Plataforma de conteúdo e práticas católicas: santos, orações, novenas, livros e liturgia reunidos em um só lugar.</p>
          <p>Trabalho de Conclusão de Curso · versão MVP. A liturgia desta versão é conteúdo de demonstração.</p>
        </div>
      </aside>
    </>
  );
}

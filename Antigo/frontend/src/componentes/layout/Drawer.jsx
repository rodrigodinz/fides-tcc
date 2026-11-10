import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";
import { MODULOS } from "../../navegacao.js";
import Icone from "../Icone.jsx";
import Ornamento from "../Ornamento.jsx";
import { prenderFoco } from "../focoPreso.js";

/** Menu lateral pela direita, com véu translúcido, foco preso, Esc e área institucional. */
export default function Drawer({ aberto, aoFechar }) {
  const ref = useRef(null);
  const refFechar = useRef(null);

  useEffect(() => {
    if (!aberto) return undefined;
    document.body.classList.add("fd-sem-rolagem");
    const t = setTimeout(() => refFechar.current?.focus(), 30);
    const aoTeclar = (e) => {
      if (e.key === "Escape") { e.preventDefault(); aoFechar(); }
      else prenderFoco(e, ref.current);
    };
    document.addEventListener("keydown", aoTeclar);
    return () => { clearTimeout(t); document.body.classList.remove("fd-sem-rolagem"); document.removeEventListener("keydown", aoTeclar); };
  }, [aberto, aoFechar]);

  return (
    <>
      <div className={`fd-veu${aberto ? " is-aberto" : ""}`} onClick={aoFechar} aria-hidden="true" />
      <aside id="fd-menu" ref={ref} className={`fd-drawer${aberto ? " is-aberto" : ""}`} role="dialog" aria-modal="true" aria-label="Menu" aria-hidden={!aberto}>
        <div className="fd-drawer__topo">
          <Ornamento tipo="curto" />
          <button ref={refFechar} type="button" className="fd-botao-icone" aria-label="Fechar menu" onClick={aoFechar}>
            <Icone nome="fechar" />
          </button>
        </div>
        <nav className="fd-drawer__nav" aria-label="Módulos">
          <ul>
            {MODULOS.map((m) => (
              <li key={m.rota}>
                <NavLink to={m.rota} end={m.fim} onClick={aoFechar}><Icone nome={m.icone} tamanho={24} />{m.nome}</NavLink>
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

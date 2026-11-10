import { forwardRef, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import simboloDoFides from "../../assets/simbolo-fides.svg";
import { Modulos } from "../../navegacao.js";
import { useDirecaoRolagem } from "../../hooks/useDirecaoRolagem.js";
import Icone from "../Icone.jsx";

// barra do topo; some ao rolar para baixo (useDirecaoRolagem)
const Navbar = forwardRef(function Navbar({ menuAberto, aoAbrirMenu }, referenciaDoBotaoMenu) {
  const [focoDentroDaNavbar, setFocoDentroDaNavbar] = useState(false);
  const navbarEscondida = useDirecaoRolagem({ rolagemPausada: menuAberto || focoDentroDaNavbar });
  const modulosDaNavbar = Modulos.filter((modulo) => modulo.aparecerNaNavbar);
  return (
    <header
      className={`fd-navbar${navbarEscondida ? " is-escondida" : ""}`}
      onFocus={() => setFocoDentroDaNavbar(true)}
      onBlur={(evento) => { if (!evento.currentTarget.contains(evento.relatedTarget)) setFocoDentroDaNavbar(false); }}
    >
      <div className="fd-navbar__inner">
        <Link to="/" className="fd-navbar__simbolo" aria-label="Fides — página inicial">
          <img src={simboloDoFides} alt="" width="34" height="46" />
        </Link>
        <Link to="/" className="fd-navbar__nome" aria-hidden="true" tabIndex={-1}>FIDES</Link>
        <div className="fd-navbar__direita">
          <nav aria-label="Principal">
            <ul className="fd-navbar__links">
              {modulosDaNavbar.map((modulo) => (
                <li key={modulo.rota}><NavLink to={modulo.rota} className="fd-navbar__link">{modulo.nome}</NavLink></li>
              ))}
            </ul>
          </nav>
          <button ref={referenciaDoBotaoMenu} type="button" className="fd-botao-icone" aria-label="Abrir menu" aria-expanded={menuAberto} aria-controls="fd-menu" onClick={aoAbrirMenu}>
            <Icone nome="menu" />
          </button>
        </div>
      </div>
    </header>
  );
});

export default Navbar;

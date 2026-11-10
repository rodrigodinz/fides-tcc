import { forwardRef, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import simbolo from "../../assets/simbolo-fides.svg";
import { MODULOS } from "../../navegacao.js";
import { useDirecaoRolagem } from "../../hooks/useDirecaoRolagem.js";
import Icone from "../Icone.jsx";

/**
 * Barra superior fixa. Símbolo à esquerda, nome "FIDES" centralizado no viewport,
 * poucos links + menu à direita. Desktop recolhe para 6px ao rolar para baixo;
 * celular some por completo. Com foco de teclado dentro dela, ela não se esconde.
 */
const Navbar = forwardRef(function Navbar({ drawerAberto, aoAbrirMenu }, refMenu) {
  const [focoDentro, setFocoDentro] = useState(false);
  const escondida = useDirecaoRolagem({ pausado: drawerAberto || focoDentro });
  const links = MODULOS.filter((m) => m.navbar);
  return (
    <header
      className={`fd-navbar${escondida ? " is-escondida" : ""}`}
      onFocus={() => setFocoDentro(true)}
      onBlur={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) setFocoDentro(false); }}
    >
      <div className="fd-navbar__inner">
        <Link to="/" className="fd-navbar__simbolo" aria-label="Fides — página inicial">
          <img src={simbolo} alt="" width="34" height="46" />
        </Link>
        <Link to="/" className="fd-navbar__nome" aria-hidden="true" tabIndex={-1}>FIDES</Link>
        <div className="fd-navbar__direita">
          <nav aria-label="Principal">
            <ul className="fd-navbar__links">
              {links.map((m) => (
                <li key={m.rota}><NavLink to={m.rota} className="fd-navbar__link">{m.nome}</NavLink></li>
              ))}
            </ul>
          </nav>
          <button ref={refMenu} type="button" className="fd-botao-icone" aria-label="Abrir menu" aria-expanded={drawerAberto} aria-controls="fd-menu" onClick={aoAbrirMenu}>
            <Icone nome="menu" />
          </button>
        </div>
      </div>
    </header>
  );
});

export default Navbar;

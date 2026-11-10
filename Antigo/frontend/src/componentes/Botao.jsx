import { forwardRef } from "react";
import { Link } from "react-router-dom";
import Icone from "./Icone.jsx";

/** Botão real (<button>) ou link com aparência de botão. variante: primario | especial | secundario | texto */
export const Botao = forwardRef(function Botao({ variante = "primario", icone, iconeDepois, pequeno, children, className = "", type = "button", ...resto }, ref) {
  return (
    <button ref={ref} type={type} className={`fd-btn fd-btn--${variante}${pequeno ? " fd-btn--pequeno" : ""} ${className}`.trim()} {...resto}>
      {icone && <Icone nome={icone} />}{children}{iconeDepois && <Icone nome={iconeDepois} />}
    </button>
  );
});

export function BotaoLink({ variante = "primario", icone, iconeDepois, pequeno, children, className = "", to, ...resto }) {
  return (
    <Link to={to} className={`fd-btn fd-btn--${variante}${pequeno ? " fd-btn--pequeno" : ""} ${className}`.trim()} {...resto}>
      {icone && <Icone nome={icone} />}{children}{iconeDepois && <Icone nome={iconeDepois} />}
    </Link>
  );
}

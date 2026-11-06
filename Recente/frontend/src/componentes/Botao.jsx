import { forwardRef } from "react";
import { Link } from "react-router-dom";
import Icone from "./Icone.jsx";

const montarClassesDoBotao = (variante, pequeno, className) =>
  `fd-btn fd-btn--${variante}${pequeno ? " fd-btn--pequeno" : ""} ${className}`.trim();

// Botão padrão do site; variante muda a cor (primario, secundario, especial, texto).
// forwardRef deixa o componente pai segurar o botão (para devolver o foco a ele).
export const Botao = forwardRef(function Botao({ variante = "primario", icone, iconeDepois, pequeno, children, className = "", type = "button", ...demaisPropriedades }, referencia) {
  return (
    <button ref={referencia} type={type} className={montarClassesDoBotao(variante, pequeno, className)} {...demaisPropriedades}>
      {icone && <Icone nome={icone} />}{children}{iconeDepois && <Icone nome={iconeDepois} />}
    </button>
  );
});

// mesmo visual do botão, mas navega para outra página (Link do React Router)
export function BotaoLink({ variante = "primario", icone, iconeDepois, pequeno, children, className = "", to, ...demaisPropriedades }) {
  return (
    <Link to={to} className={montarClassesDoBotao(variante, pequeno, className)} {...demaisPropriedades}>
      {icone && <Icone nome={icone} />}{children}{iconeDepois && <Icone nome={iconeDepois} />}
    </Link>
  );
}

/**
 * Ícones lineares do Fides: grade 24px, traço 1,5px, pontas arredondadas, cor herdada.
 * Módulos e momentos do dia são desenhos próprios; os de interface seguem a mesma grade.
 */
import { PATHS } from "./iconesDados.jsx";

export default function Icone({ nome, tamanho, rotulo, className = "" }) {
  const conteudo = PATHS[nome];
  if (!conteudo) return null;
  const acessivel = rotulo ? { role: "img", "aria-label": rotulo } : { "aria-hidden": "true", focusable: "false" };
  return (
    <svg className={`fd-ico ${tamanho === 24 ? "fd-ico--24" : ""} ${className}`.trim()} viewBox="0 0 24 24" {...acessivel}>
      {conteudo}
    </svg>
  );
}

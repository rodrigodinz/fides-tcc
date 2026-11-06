import { Desenhos_Dos_Icones } from "./iconesDados.jsx";

// desenha o ícone pelo nome; os desenhos ficam em iconesDados.jsx
export default function Icone({ nome, tamanho, rotulo, className = "" }) {
  const desenhoDoIcone = Desenhos_Dos_Icones[nome];
  if (!desenhoDoIcone) return null;
  const propriedadesDeAcessibilidade = rotulo ? { role: "img", "aria-label": rotulo } : { "aria-hidden": "true", focusable: "false" };
  return (
    <svg className={`fd-ico ${tamanho === 24 ? "fd-ico--24" : ""} ${className}`.trim()} viewBox="0 0 24 24" {...propriedadesDeAcessibilidade}>
      {desenhoDoIcone}
    </svg>
  );
}

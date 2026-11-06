/**
 * Ornamentos rococó (SVG vetorial, decorativos). Família A: estrutura; Família B: destaque.
 * Referências: cartelas e estuques rocaille (volutas, C/S, acanto, concha e cabochão).
 */
import crista from "../assets/ornamentos/crista-acanto-familia-b.svg";
import titulo from "../assets/ornamentos/titulo-familia-b.svg";
import divisor from "../assets/ornamentos/divisor-familia-a.svg";
import curto from "../assets/ornamentos/divisor-curto-familia-a.svg";

const FONTES = { crista, titulo, divisor, curto };
const PROPORCAO = { crista: [372, 60], titulo: [516, 40], divisor: [464, 26], curto: [200, 20] };

export default function Ornamento({ tipo = "divisor", className = "" }) {
  const [w, h] = PROPORCAO[tipo];
  return <img className={`fd-orn fd-orn--${tipo} ${className}`.trim()} src={FONTES[tipo]} width={w} height={h} alt="" aria-hidden="true" />;
}

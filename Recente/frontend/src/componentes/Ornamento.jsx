import cristaDeAcanto from "../assets/ornamentos/crista-acanto-familia-b.svg";
import ornamentoDeTitulo from "../assets/ornamentos/titulo-familia-b.svg";
import divisorLongo from "../assets/ornamentos/divisor-familia-a.svg";
import divisorCurto from "../assets/ornamentos/divisor-curto-familia-a.svg";

const Arquivos_Dos_Ornamentos = { crista: cristaDeAcanto, titulo: ornamentoDeTitulo, divisor: divisorLongo, curto: divisorCurto };
const Dimensoes_Dos_Ornamentos = { crista: [372, 60], titulo: [516, 40], divisor: [464, 26], curto: [200, 20] };

export default function Ornamento({ tipo = "divisor", className = "" }) {
  const [largura, altura] = Dimensoes_Dos_Ornamentos[tipo];
  return <img className={`fd-orn fd-orn--${tipo} ${className}`.trim()} src={Arquivos_Dos_Ornamentos[tipo]} width={largura} height={altura} alt="" aria-hidden="true" />;
}

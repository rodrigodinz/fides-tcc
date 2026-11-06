import { Link } from "react-router-dom";
import RetratoSanto from "./RetratoSanto.jsx";
import Icone from "./Icone.jsx";

// card do santo com retrato; o card inteiro é clicável
export default function CardSanto({ santo, nivel = 3 }) {
  const TagDoTitulo = `h${nivel}`;
  return (
    <article className="fd-card fd-card-santo">
      <RetratoSanto fotoUrl={santo.foto_url} nome={santo.nome} decorativo />
      <div className="fd-card-santo__corpo">
        <TagDoTitulo className="fd-card-santo__nome">
          <Link to={`/santos/${santo.id}`} className="fd-card__link-total">{santo.nome}</Link>
        </TagDoTitulo>
        <span className="fd-card-santo__mais" aria-hidden="true">Ver vida e devoções <Icone nome="direita" /></span>
      </div>
    </article>
  );
}

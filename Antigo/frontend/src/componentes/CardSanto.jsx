import { Link } from "react-router-dom";
import RetratoSanto from "./RetratoSanto.jsx";
import Icone from "./Icone.jsx";

/** Card de santo: retrato + nome; o card inteiro leva à página do santo. */
export default function CardSanto({ santo, nivel = 3 }) {
  const Titulo = `h${nivel}`;
  return (
    <article className="fd-card fd-card-santo">
      <RetratoSanto fotoUrl={santo.foto_url} nome={santo.nome} decorativo />
      <div className="fd-card-santo__corpo">
        <Titulo className="fd-card-santo__nome">
          <Link to={`/santos/${santo.id}`} className="fd-card__link-total">{santo.nome}</Link>
        </Titulo>
        <span className="fd-card-santo__mais" aria-hidden="true">Ver vida e devoções <Icone nome="direita" /></span>
      </div>
    </article>
  );
}

import { Link } from "react-router-dom";

/**
 * Card do Fides. Comum: branco, dois cantos rococó, sem contorno.
 * Destaque: quatro cantos e contorno dourado fino.
 * Com `para`, a superfície inteira navega (o título é o link; ::after cobre o card).
 */
export default function Card({ destaque, simples, para, titulo, nivel = 3, rotulo, meta, acoes, children, className = "", ...resto }) {
  const Titulo = `h${nivel}`;
  const classes = ["fd-card", destaque && "fd-card--destaque", simples && "fd-card--simples", className].filter(Boolean).join(" ");
  return (
    <article className={classes} {...resto}>
      {destaque && <span className="fd-card__cantos" aria-hidden="true" />}
      {rotulo && <p className="fd-rotulo">{rotulo}</p>}
      {titulo && (
        <Titulo className="fd-card__titulo" style={rotulo ? { marginTop: 4 } : undefined}>
          {para ? <Link to={para} className="fd-card__link-total">{titulo}</Link> : titulo}
        </Titulo>
      )}
      {meta && <p className="fd-aux fd-card__meta">{meta}</p>}
      {children}
      {acoes && <div className="fd-card__acoes fd-card__acima">{acoes}</div>}
    </article>
  );
}

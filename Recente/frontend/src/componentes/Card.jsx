import { Link } from "react-router-dom";

// Caixa de conteúdo usada em todo o site. As "props" (destaque, titulo, para, acoes...) são
// os parâmetros que a página passa, como argumentos de uma função.
export default function Card({ destaque, simples, para, titulo, nivel = 3, rotulo, meta, acoes, children, className = "", ...demaisPropriedades }) {
  // escolhe h2, h3... conforme a hierarquia da página (acessibilidade)
  const TagDoTitulo = `h${nivel}`;
  const classesDoCard = ["fd-card", destaque && "fd-card--destaque", simples && "fd-card--simples", className].filter(Boolean).join(" ");
  return (
    <article className={classesDoCard} {...demaisPropriedades}>
      {destaque && <span className="fd-card__cantos" aria-hidden="true" />}
      {rotulo && <p className="fd-rotulo">{rotulo}</p>}
      {titulo && (
        <TagDoTitulo className="fd-card__titulo" style={rotulo ? { marginTop: 4 } : undefined}>
          {para ? <Link to={para} className="fd-card__link-total">{titulo}</Link> : titulo}
        </TagDoTitulo>
      )}
      {meta && <p className="fd-aux fd-card__meta">{meta}</p>}
      {children}
      {acoes && <div className="fd-card__acoes fd-card__acima">{acoes}</div>}
    </article>
  );
}

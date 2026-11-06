import { Link } from "react-router-dom";
import Ornamento from "./Ornamento.jsx";

/** Abertura de página: ornamento acima do título (Família B), rótulo, H1 centralizado e texto curto. */
export function CabecalhoPagina({ titulo, rotulo, lead, ornamento = "titulo", children, alinhamento }) {
  return (
    <header className={`fd-cabecalho${alinhamento === "esquerda" ? " fd-cabecalho--esquerda" : ""}`}>
      {ornamento && <Ornamento tipo={ornamento} />}
      {rotulo && <span className="fd-rotulo">{rotulo}</span>}
      <h1 className="fd-h1">{titulo}</h1>
      {lead && <p className="fd-cabecalho__lead">{lead}</p>}
      {children}
    </header>
  );
}

/** Título de seção (H2) com divisor curto da Família A. */
export function TituloSecao({ titulo, id, descricao, acao, nivel = 2 }) {
  const T = `h${nivel}`;
  return (
    <div className="fd-secao-titulo">
      <Ornamento tipo="curto" />
      <div className="fd-secao-titulo__linha">
        <T className={nivel === 2 ? "fd-h2" : "fd-h3"} id={id}>{titulo}</T>
        {acao}
      </div>
      {descricao && <p className="fd-aux">{descricao}</p>}
    </div>
  );
}

/** Migalhas de pão para retorno contextual. `itens`: [{texto, para?}] */
export function Migalhas({ itens }) {
  return (
    <nav className="fd-migalhas" aria-label="Você está em">
      <ol>
        {itens.map((it, i) => (
          <li key={`${it.texto}-${i}`}>
            {it.para && i < itens.length - 1 ? <Link to={it.para}>{it.texto}</Link> : <span aria-current={i === itens.length - 1 ? "page" : undefined}>{it.texto}</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}

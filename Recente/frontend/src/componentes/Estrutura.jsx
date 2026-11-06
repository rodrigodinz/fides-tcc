import { Link } from "react-router-dom";
import Ornamento from "./Ornamento.jsx";

// título da página com o ornamento dourado em cima
export function CabecalhoPagina({ titulo, rotulo, textoDeAbertura, ornamento = "titulo", children, alinhamento }) {
  return (
    <header className={`fd-cabecalho${alinhamento === "esquerda" ? " fd-cabecalho--esquerda" : ""}`}>
      {ornamento && <Ornamento tipo={ornamento} />}
      {rotulo && <span className="fd-rotulo">{rotulo}</span>}
      <h1 className="fd-h1">{titulo}</h1>
      {textoDeAbertura && <p className="fd-cabecalho__lead">{textoDeAbertura}</p>}
      {children}
    </header>
  );
}

export function TituloSecao({ titulo, id, descricao, acao, nivel = 2 }) {
  const TagDoTitulo = `h${nivel}`;
  return (
    <div className="fd-secao-titulo">
      <Ornamento tipo="curto" />
      <div className="fd-secao-titulo__linha">
        <TagDoTitulo className={nivel === 2 ? "fd-h2" : "fd-h3"} id={id}>{titulo}</TagDoTitulo>
        {acao}
      </div>
      {descricao && <p className="fd-aux">{descricao}</p>}
    </div>
  );
}

// trilha "Início · Novenas · Novena X" no topo das páginas de detalhe
export function Migalhas({ itens }) {
  return (
    <nav className="fd-migalhas" aria-label="Você está em">
      <ol>
        {itens.map((item, posicao) => {
          const ehUltimoItem = posicao === itens.length - 1;
          return (
            <li key={`${item.texto}-${posicao}`}>
              {item.para && !ehUltimoItem
                ? <Link to={item.para}>{item.texto}</Link>
                : <span aria-current={ehUltimoItem ? "page" : undefined}>{item.texto}</span>}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

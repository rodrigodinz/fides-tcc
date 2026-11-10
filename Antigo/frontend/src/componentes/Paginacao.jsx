import { paginasVisiveis } from "../utils/paginacao.js";
import Icone from "./Icone.jsx";

/** Página atual, até duas antes e duas depois; Anterior/Próxima nas extremidades. */
export default function Paginacao({ pagina, totalPaginas, total, aoMudar, rotulo = "Paginação" }) {
  if (!totalPaginas || totalPaginas <= 1) return null;
  const numeros = paginasVisiveis(pagina, totalPaginas);
  return (
    <nav className="fd-paginacao" aria-label={rotulo}>
      <ol>
        <li>
          <button type="button" className="fd-pag fd-pag--seta" disabled={pagina <= 1} onClick={() => aoMudar(pagina - 1)} aria-label="Página anterior">
            <Icone nome="esquerda" /><span>Anterior</span>
          </button>
        </li>
        {numeros.map((n) => (
          <li key={n}>
            <button type="button" className="fd-pag" aria-current={n === pagina ? "page" : undefined} aria-label={`Página ${n}`} onClick={() => n !== pagina && aoMudar(n)}>{n}</button>
          </li>
        ))}
        <li>
          <button type="button" className="fd-pag fd-pag--seta" disabled={pagina >= totalPaginas} onClick={() => aoMudar(pagina + 1)} aria-label="Próxima página">
            <span>Próxima</span><Icone nome="direita" />
          </button>
        </li>
      </ol>
      {typeof total === "number" && <p className="fd-aux fd-paginacao__resumo">Página {pagina} de {totalPaginas} · {total} {total === 1 ? "item" : "itens"}</p>}
    </nav>
  );
}

import { calcularPaginasVisiveis } from "../utils/paginacao.js";
import Icone from "./Icone.jsx";

// botões Anterior / números / Próxima; com uma página só, não aparece
export default function Paginacao({ pagina, totalPaginas, totalRegistros, aoMudarPagina, rotulo = "Paginação" }) {
  if (!totalPaginas || totalPaginas <= 1) return null;
  const paginasVisiveis = calcularPaginasVisiveis(pagina, totalPaginas);
  return (
    <nav className="fd-paginacao" aria-label={rotulo}>
      <ol>
        <li>
          <button type="button" className="fd-pag fd-pag--seta" disabled={pagina <= 1} onClick={() => aoMudarPagina(pagina - 1)} aria-label="Página anterior">
            <Icone nome="esquerda" /><span>Anterior</span>
          </button>
        </li>
        {paginasVisiveis.map((numeroDaPagina) => (
          <li key={numeroDaPagina}>
            <button type="button" className="fd-pag" aria-current={numeroDaPagina === pagina ? "page" : undefined} aria-label={`Página ${numeroDaPagina}`}
              onClick={() => numeroDaPagina !== pagina && aoMudarPagina(numeroDaPagina)}>{numeroDaPagina}</button>
          </li>
        ))}
        <li>
          <button type="button" className="fd-pag fd-pag--seta" disabled={pagina >= totalPaginas} onClick={() => aoMudarPagina(pagina + 1)} aria-label="Próxima página">
            <span>Próxima</span><Icone nome="direita" />
          </button>
        </li>
      </ol>
      {typeof totalRegistros === "number" && (
        <p className="fd-aux fd-paginacao__resumo">Página {pagina} de {totalPaginas} · {totalRegistros} {totalRegistros === 1 ? "item" : "itens"}</p>
      )}
    </nav>
  );
}

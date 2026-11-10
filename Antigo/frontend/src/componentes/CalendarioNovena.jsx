import { Link } from "react-router-dom";
import { dataCurta } from "../utils/datas.js";

/**
 * Nove círculos numerados. Três informações independentes:
 *  - "Hoje" (anel dourado): dia atual pela Agenda global da API;
 *  - "Rezado" (verde + check): marcação pessoal guardada neste dispositivo;
 *  - selecionado (contorno azul): o dia aberto na tela.
 * Nunca só pela cor: cada estado também vai em texto acessível.
 */
export default function CalendarioNovena({ novenaId, dias, diaAtual, marcados = [], selecionado, comLegenda = true }) {
  return (
    <>
      <ol className="fd-calendario" aria-label="Os nove dias da novena">
        {dias.map((d) => {
          const hoje = diaAtual === d.numero_dia;
          const marcado = marcados.includes(d.numero_dia);
          const sel = selecionado === d.numero_dia;
          const partes = [`Dia ${d.numero_dia}`, d.data ? dataCurta(d.data) : null, hoje ? "dia atual da agenda" : null, marcado ? "marcado como rezado neste dispositivo" : null, sel ? "aberto" : null].filter(Boolean);
          const classes = ["fd-dia", hoje && "is-hoje", marcado && "is-marcado", sel && "is-selecionado"].filter(Boolean).join(" ");
          return (
            <li key={d.numero_dia} className={classes}>
              <Link to={`/novenas/${novenaId}/dia/${d.numero_dia}`} className="fd-dia__circulo" aria-label={partes.join(", ")} aria-current={sel ? "step" : undefined}>
                {d.numero_dia}
              </Link>
              <span className="fd-dia__data" aria-hidden="true">{d.data ? dataCurta(d.data) : "—"}</span>
              <span className="fd-dia__hoje" aria-hidden="true">{hoje ? "Hoje" : ""}</span>
            </li>
          );
        })}
      </ol>
      {comLegenda && (
        <ul className="fd-legenda" aria-label="Legenda">
          <li><i className="h" />Dia atual (agenda da novena)</li>
          <li><i className="m" />Rezado (marcado neste dispositivo)</li>
          <li><i className="s" />Dia aberto</li>
          <li><i />Demais dias</li>
        </ul>
      )}
    </>
  );
}

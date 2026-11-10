import { Link } from "react-router-dom";
import { escreverDataCurta } from "../utils/datas.js";

// Os 9 dias da novena em círculos. Cada dia pode estar: hoje (agenda), marcado (rezado
// neste aparelho) ou selecionado (aberto na tela). O texto do aria-label é o que o leitor de tela lê.
export default function CalendarioNovena({ novenaId, dias, diaAtual, marcados = [], diaSelecionado, comLegenda = true }) {
  return (
    <>
      <ol className="fd-calendario" aria-label="Os nove dias da novena">
        {/* .map transforma a lista de dias em uma lista de <li>; o key ajuda o React a saber qual item mudou */}
        {dias.map((dia) => {
          const ehHoje = diaAtual === dia.numero_do_dia;
          const estaMarcado = marcados.includes(dia.numero_do_dia);
          const estaSelecionado = diaSelecionado === dia.numero_do_dia;
          const descricaoAcessivel = [
            `Dia ${dia.numero_do_dia}`,
            dia.data ? escreverDataCurta(dia.data) : null,
            ehHoje ? "dia atual da agenda" : null,
            estaMarcado ? "marcado como rezado neste dispositivo" : null,
            estaSelecionado ? "aberto" : null,
          ].filter(Boolean);
          const classesDoDia = ["fd-dia", ehHoje && "is-hoje", estaMarcado && "is-marcado", estaSelecionado && "is-selecionado"].filter(Boolean).join(" ");
          return (
            <li key={dia.numero_do_dia} className={classesDoDia}>
              <Link to={`/novenas/${novenaId}/dia/${dia.numero_do_dia}`} className="fd-dia__circulo" aria-label={descricaoAcessivel.join(", ")} aria-current={estaSelecionado ? "step" : undefined}>
                {dia.numero_do_dia}
              </Link>
              <span className="fd-dia__data" aria-hidden="true">{dia.data ? escreverDataCurta(dia.data) : "—"}</span>
              <span className="fd-dia__hoje" aria-hidden="true">{ehHoje ? "Hoje" : ""}</span>
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

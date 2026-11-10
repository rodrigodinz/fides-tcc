import { useId } from "react";
import Icone from "./Icone.jsx";

/** Campo de busca limpo com lupa e botão de limpar. */
export function CampoBusca({ rotulo, valor, aoMudar, placeholder, ajuda, id }) {
  const gerado = useId();
  const idCampo = id ?? `busca-${gerado}`;
  return (
    <div className="fd-campo">
      <label htmlFor={idCampo}>{rotulo}</label>
      <div className="fd-busca" role="search">
        <Icone nome="lupa" />
        <input id={idCampo} className="fd-input" type="search" value={valor} placeholder={placeholder} autoComplete="off" spellCheck="false"
          onChange={(e) => aoMudar(e.target.value)} aria-describedby={ajuda ? `${idCampo}-ajuda` : undefined} />
        {valor && (
          <button type="button" className="fd-botao-icone fd-busca__limpar" aria-label="Limpar busca" onClick={() => aoMudar("")}>
            <Icone nome="fechar" />
          </button>
        )}
      </div>
      {ajuda && <span id={`${idCampo}-ajuda`} className="fd-aux">{ajuda}</span>}
    </div>
  );
}

/** Dropdown nativo estilizado. `opcoes`: [{valor, rotulo}] */
export function Seletor({ rotulo, valor, aoMudar, opcoes, todas = "Todos", desabilitado, id }) {
  const gerado = useId();
  const idCampo = id ?? `sel-${gerado}`;
  return (
    <div className="fd-campo">
      <label htmlFor={idCampo}>{rotulo}</label>
      <select id={idCampo} className="fd-select" value={valor ?? ""} onChange={(e) => aoMudar(e.target.value)} disabled={desabilitado}>
        <option value="">{todas}</option>
        {opcoes.map((o) => <option key={o.valor} value={o.valor}>{o.rotulo}</option>)}
      </select>
    </div>
  );
}

/** Chips de seleção única (podem ser desmarcados). `opcoes`: [{valor, rotulo, icone}] */
export function Chips({ rotulo, valor, aoMudar, opcoes }) {
  const gerado = useId();
  return (
    <div className="fd-campo">
      <span className="fd-campo__rotulo" id={`chips-${gerado}`}>{rotulo}</span>
      <div className="fd-chips" role="group" aria-labelledby={`chips-${gerado}`}>
        {opcoes.map((o) => {
          const ativo = String(valor) === String(o.valor);
          return (
            <button key={o.valor} type="button" className="fd-chip" aria-pressed={ativo} onClick={() => aoMudar(ativo ? "" : String(o.valor))}>
              {o.icone && <Icone nome={o.icone} />}{o.rotulo}
            </button>
          );
        })}
      </div>
    </div>
  );
}

import { useId } from "react";
import Icone from "./Icone.jsx";

// campo de busca "controlado": o valor vem da página e cada tecla chama aoMudar
export function CampoBusca({ rotulo, valor, aoMudar, placeholder, ajuda, id }) {
  // useId gera um id único para ligar o <label> ao <input>
  const idGerado = useId();
  const idDoCampo = id ?? `busca-${idGerado}`;
  return (
    <div className="fd-campo">
      <label htmlFor={idDoCampo}>{rotulo}</label>
      <div className="fd-busca" role="search">
        <Icone nome="lupa" />
        <input id={idDoCampo} className="fd-input" type="search" value={valor} placeholder={placeholder} autoComplete="off" spellCheck="false"
          onChange={(evento) => aoMudar(evento.target.value)} aria-describedby={ajuda ? `${idDoCampo}-ajuda` : undefined} />
        {valor && (
          <button type="button" className="fd-botao-icone fd-busca__limpar" aria-label="Limpar busca" onClick={() => aoMudar("")}>
            <Icone nome="fechar" />
          </button>
        )}
      </div>
      {ajuda && <span id={`${idDoCampo}-ajuda`} className="fd-aux">{ajuda}</span>}
    </div>
  );
}

// caixa de seleção (select) usada nos filtros por santo e tipo
export function Seletor({ rotulo, valor, aoMudar, opcoes, textoDeTodos = "Todos", desabilitado, id }) {
  const idGerado = useId();
  const idDoCampo = id ?? `sel-${idGerado}`;
  return (
    <div className="fd-campo">
      <label htmlFor={idDoCampo}>{rotulo}</label>
      <select id={idDoCampo} className="fd-select" value={valor ?? ""} onChange={(evento) => aoMudar(evento.target.value)} disabled={desabilitado}>
        <option value="">{textoDeTodos}</option>
        {opcoes.map((opcao) => <option key={opcao.valor} value={opcao.valor}>{opcao.rotulo}</option>)}
      </select>
    </div>
  );
}

// botões de filtro liga/desliga (momentos do dia); clicar de novo desmarca
export function Chips({ rotulo, valor, aoMudar, opcoes }) {
  const idGerado = useId();
  return (
    <div className="fd-campo">
      <span className="fd-campo__rotulo" id={`chips-${idGerado}`}>{rotulo}</span>
      <div className="fd-chips" role="group" aria-labelledby={`chips-${idGerado}`}>
        {opcoes.map((opcao) => {
          const chipAtivo = String(valor) === String(opcao.valor);
          return (
            <button key={opcao.valor} type="button" className="fd-chip" aria-pressed={chipAtivo} onClick={() => aoMudar(chipAtivo ? "" : String(opcao.valor))}>
              {opcao.icone && <Icone nome={opcao.icone} />}{opcao.rotulo}
            </button>
          );
        })}
      </div>
    </div>
  );
}

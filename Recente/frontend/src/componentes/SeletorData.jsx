import { useId } from "react";
import { escreverDataCurta, somarDias } from "../utils/datas.js";
import { Botao } from "./Botao.jsx";

// dia anterior / calendário / próximo dia, travado no período que a API informou (hoje ± 7)
export default function SeletorData({ data, periodo, aoMudarData }) {
  const idGerado = useId();
  if (!periodo) return null;
  const diaAnterior = somarDias(data, -1);
  const proximoDia = somarDias(data, 1);
  return (
    <div className="fd-seletor-data">
      <Botao variante="secundario" icone="esquerda" disabled={diaAnterior < periodo.inicio} onClick={() => aoMudarData(diaAnterior)}
        aria-label={`Dia anterior (${escreverDataCurta(diaAnterior)})`}>{escreverDataCurta(diaAnterior)}</Botao>
      <div className="fd-campo">
        <label htmlFor={`data-${idGerado}`}>Escolher data</label>
        <input id={`data-${idGerado}`} className="fd-input" type="date" value={data} min={periodo.inicio} max={periodo.fim}
          onChange={(evento) => { const dataEscolhida = evento.target.value; if (dataEscolhida) aoMudarData(dataEscolhida); }} />
      </div>
      <Botao variante="secundario" iconeDepois="direita" disabled={proximoDia > periodo.fim} onClick={() => aoMudarData(proximoDia)}
        aria-label={`Próximo dia (${escreverDataCurta(proximoDia)})`}>{escreverDataCurta(proximoDia)}</Botao>
      <p className="fd-aux fd-seletor-data__janela">
        Período disponível: {escreverDataCurta(periodo.inicio)} a {escreverDataCurta(periodo.fim)} (hoje ± 7 dias).
        {data !== periodo.hoje && <> <button type="button" className="fd-btn fd-btn--texto fd-btn--pequeno" onClick={() => aoMudarData(periodo.hoje)}>Voltar para hoje</button></>}
      </p>
    </div>
  );
}

import { useId } from "react";
import { dataCurta, somarDias } from "../utils/datas.js";
import { Botao } from "./Botao.jsx";

/** Data limitada à janela da API (intervalo.inicio..intervalo.fim = hoje ± 7 dias). */
export default function SeletorData({ data, intervalo, aoMudar }) {
  const id = useId();
  if (!intervalo) return null;
  const anterior = somarDias(data, -1);
  const proxima = somarDias(data, 1);
  return (
    <div className="fd-seletor-data">
      <Botao variante="secundario" icone="esquerda" disabled={anterior < intervalo.inicio} onClick={() => aoMudar(anterior)} aria-label={`Dia anterior (${dataCurta(anterior)})`}>{dataCurta(anterior)}</Botao>
      <div className="fd-campo">
        <label htmlFor={`data-${id}`}>Escolher data</label>
        <input id={`data-${id}`} className="fd-input" type="date" value={data} min={intervalo.inicio} max={intervalo.fim}
          onChange={(e) => { const v = e.target.value; if (v) aoMudar(v); }} />
      </div>
      <Botao variante="secundario" iconeDepois="direita" disabled={proxima > intervalo.fim} onClick={() => aoMudar(proxima)} aria-label={`Próximo dia (${dataCurta(proxima)})`}>{dataCurta(proxima)}</Botao>
      <p className="fd-aux fd-seletor-data__janela">
        Período disponível: {dataCurta(intervalo.inicio)} a {dataCurta(intervalo.fim)} (hoje ± 7 dias).
        {data !== intervalo.hoje && <> <button type="button" className="fd-btn fd-btn--texto fd-btn--pequeno" onClick={() => aoMudar(intervalo.hoje)}>Voltar para hoje</button></>}
      </p>
    </div>
  );
}

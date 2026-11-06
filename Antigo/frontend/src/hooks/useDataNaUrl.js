import { useSearchParams } from "react-router-dom";
import { ehDataIso } from "../utils/datas.js";

/** ?data=AAAA-MM-DD na URL (recarregável e compartilhável). Ausente = hoje, decidido pela API. */
export function useDataNaUrl() {
  const [params, setParams] = useSearchParams();
  const bruto = params.get("data");
  const data = bruto && ehDataIso(bruto) ? bruto : undefined;
  const invalida = Boolean(bruto) && !data;
  const definir = (iso, { hoje } = {}) => {
    const n = new URLSearchParams(params);
    if (!iso || iso === hoje) n.delete("data"); else n.set("data", iso);
    setParams(n);
  };
  return { data, invalida, definir };
}

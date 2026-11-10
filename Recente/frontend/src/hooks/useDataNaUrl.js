import { useSearchParams } from "react-router-dom";
import { ehDataIso } from "../utils/datas.js";

// lê e grava a data escolhida na URL (?data=AAAA-MM-DD), assim o link pode ser compartilhado
export function useDataNaUrl() {
  const [parametrosDaUrl, setParametrosDaUrl] = useSearchParams();
  const dataEscritaNaUrl = parametrosDaUrl.get("data");
  const data = dataEscritaNaUrl && ehDataIso(dataEscritaNaUrl) ? dataEscritaNaUrl : undefined;
  const dataInvalida = Boolean(dataEscritaNaUrl) && !data;
  const definirData = (dataIso, { hoje } = {}) => {
    const novosParametros = new URLSearchParams(parametrosDaUrl);
    if (!dataIso || dataIso === hoje) novosParametros.delete("data"); else novosParametros.set("data", dataIso);
    setParametrosDaUrl(novosParametros);
  };
  return { data, dataInvalida, definirData };
}

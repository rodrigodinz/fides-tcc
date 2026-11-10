import { ehDataIso } from "./datas.js";
import { lerParametrosDaUrl, atualizarParametrosDaUrl } from "./url.js";

// lê a data escolhida na URL (?data=AAAA-MM-DD); sem data = hoje
export function lerDataDaUrl() {
  const dataEscritaNaUrl = lerParametrosDaUrl().get("data");
  const data = dataEscritaNaUrl && ehDataIso(dataEscritaNaUrl) ? dataEscritaNaUrl : undefined;
  return { data, dataInvalida: Boolean(dataEscritaNaUrl) && !data };
}

// grava a data na URL; se for hoje, tira o parâmetro (o link fica limpo)
export function definirDataNaUrl(dataIso, { hoje } = {}) {
  const parametrosDaUrl = lerParametrosDaUrl();
  if (!dataIso || dataIso === hoje) parametrosDaUrl.delete("data"); else parametrosDaUrl.set("data", dataIso);
  atualizarParametrosDaUrl(parametrosDaUrl);
}

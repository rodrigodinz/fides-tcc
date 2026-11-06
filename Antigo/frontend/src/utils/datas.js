/** Datas ISO (AAAA-MM-DD) tratadas como datas locais, sem fuso. */
const ISO = /^(\d{4})-(\d{2})-(\d{2})$/;

export function ehDataIso(texto) {
  const m = typeof texto === "string" && ISO.exec(texto);
  if (!m) return false;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return d.getFullYear() === Number(m[1]) && d.getMonth() === Number(m[2]) - 1 && d.getDate() === Number(m[3]);
}

export function paraData(iso) {
  const [a, m, d] = iso.split("-").map(Number);
  return new Date(a, m - 1, d);
}

export function paraIso(data) {
  const p = (n) => String(n).padStart(2, "0");
  return `${data.getFullYear()}-${p(data.getMonth() + 1)}-${p(data.getDate())}`;
}

export function somarDias(iso, dias) {
  const d = paraData(iso);
  d.setDate(d.getDate() + dias);
  return paraIso(d);
}

const capitalizar = (s) => s.charAt(0).toUpperCase() + s.slice(1);

/** "Quinta-feira, 5 de novembro de 2026" */
export function dataPorExtenso(iso, { semana = true, ano = true } = {}) {
  if (!ehDataIso(iso)) return "";
  const texto = new Intl.DateTimeFormat("pt-BR", { weekday: semana ? "long" : undefined, day: "numeric", month: "long", year: ano ? "numeric" : undefined }).format(paraData(iso));
  return capitalizar(texto);
}

/** "05/11" */
export function dataCurta(iso) {
  if (!ehDataIso(iso)) return "";
  const [, m, d] = iso.split("-");
  return `${d}/${m}`;
}

export function dentroDoIntervalo(iso, intervalo) {
  return Boolean(intervalo) && ehDataIso(iso) && iso >= intervalo.inicio && iso <= intervalo.fim;
}

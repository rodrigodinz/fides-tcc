/** Ordem canônica dos blocos da Liturgia das Horas. */
export const ORDEM_BLOCOS = ["laudes", "horas_medias", "vesperas"];
export const ordenarHoras = (horas) => [...horas].sort((a, b) => ORDEM_BLOCOS.indexOf(a.bloco.codigo) - ORDEM_BLOCOS.indexOf(b.bloco.codigo));

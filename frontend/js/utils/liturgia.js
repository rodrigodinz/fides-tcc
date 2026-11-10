export const Ordem_Dos_Blocos_Da_Liturgia = ["laudes", "horas_medias", "vesperas"];

// garante a ordem Laudes → Horas médias → Vésperas
export const ordenarHorasDaLiturgia = (horasDaLiturgia) => [...horasDaLiturgia].sort(
  (horaA, horaB) => Ordem_Dos_Blocos_Da_Liturgia.indexOf(horaA.bloco.codigo) - Ordem_Dos_Blocos_Da_Liturgia.indexOf(horaB.bloco.codigo),
);

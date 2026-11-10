// Lista única dos módulos do site; a navbar, o menu lateral e o rodapé são montados a partir dela.
export const Modulos = [
  { rota: "/", nome: "Início", icone: "inicio", rotaExata: true },
  { rota: "/santos", nome: "Santos", icone: "santos", aparecerNaNavbar: true },
  { rota: "/oracoes", nome: "Orações", icone: "oracoes", aparecerNaNavbar: true },
  { rota: "/novenas", nome: "Novenas", icone: "novenas", aparecerNaNavbar: true },
  { rota: "/livros", nome: "Livros", icone: "livros" },
  { rota: "/liturgia", nome: "Liturgia do Dia", icone: "liturgia", rotaExata: true },
  { rota: "/liturgia/horas", nome: "Liturgia das Horas", icone: "horas" },
  { rota: "/agenda", nome: "Agenda do dia", icone: "hoje" },
];

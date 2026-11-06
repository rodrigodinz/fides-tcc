/**
 * Mapa de navegação do Fides. Só módulos que existem no MVP.
 * `navbar: true` marca os poucos links visíveis na barra (decisão técnica reversível:
 * Santos e Orações são o núcleo prioritário do MVP; Novenas foi a 2ª função mais valorizada
 * no levantamento). O restante fica no drawer.
 */
export const MODULOS = [
  { rota: "/", nome: "Início", icone: "inicio", fim: true },
  { rota: "/santos", nome: "Santos", icone: "santos", navbar: true },
  { rota: "/oracoes", nome: "Orações", icone: "oracoes", navbar: true },
  { rota: "/novenas", nome: "Novenas", icone: "novenas", navbar: true },
  { rota: "/livros", nome: "Livros", icone: "livros" },
  { rota: "/liturgia", nome: "Liturgia do Dia", icone: "liturgia", fim: true },
  { rota: "/liturgia/horas", nome: "Liturgia das Horas", icone: "horas" },
  { rota: "/agenda", nome: "Agenda do dia", icone: "hoje" },
];

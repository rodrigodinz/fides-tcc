// Desenhos dos ícones (grade 24x24), guardados como texto SVG.
// A função icone() coloca o desenho dentro de um <svg> com a classe fd-ico.
export const Desenhos_Dos_Icones = {
  inicio: '<path d="M4 10.5L12 4l8 6.5"></path><path d="M6 9v10.5h12V9"></path><path d="M10 19.5v-5h4v5"></path>',
  hoje: '<rect x="3.5" y="5" width="17" height="15.5" rx="1.8"></rect><path d="M3.5 9.8h17M8 3.2v3.6M16 3.2v3.6"></path><path d="M12 12.6l.9 1.9 2 .3-1.45 1.4.35 2-1.8-.95-1.8.95.35-2-1.45-1.4 2-.3z" stroke-width="1.1"></path>',
  santos: '<ellipse cx="12" cy="4.6" rx="4.4" ry="1.5"></ellipse><circle cx="12" cy="10.2" r="3.3"></circle><path d="M5 21c.4-3.9 3.3-6.6 7-6.6s6.6 2.7 7 6.6"></path>',
  oracoes: '<path d="M12 2.8c1.7 1.9 2.3 3.2 2.3 4.3a2.3 2.3 0 0 1-4.6 0c0-1.1.6-2.4 2.3-4.3z"></path><path d="M12 9.4v1.1"></path><rect x="9.3" y="10.5" width="5.4" height="9.5" rx=".8"></rect><path d="M6.5 20.6h11"></path>',
  novenas: '<circle cx="6" cy="6" r="1.7"></circle><circle cx="12" cy="6" r="1.7"></circle><circle cx="18" cy="6" r="1.7"></circle><circle cx="6" cy="12" r="1.7"></circle><circle cx="12" cy="12" r="1.7"></circle><circle cx="18" cy="12" r="1.7"></circle><circle cx="6" cy="18" r="1.7"></circle><circle cx="12" cy="18" r="1.7"></circle><circle cx="18" cy="18" r="1.7"></circle>',
  liturgia: '<path d="M2.8 6.4c3.1-1.3 6.2-1.1 9.2.9 3-2 6.1-2.2 9.2-.9v12.4c-3.1-1.3-6.2-1.1-9.2.9-3-2-6.1-2.2-9.2-.9z"></path><path d="M12 7.3v12.4"></path><path d="M15.6 6.2v6.3l1.4-1.1 1.4 1.1V5.9" stroke-width="1.2"></path>',
  horas: '<circle cx="12" cy="12" r="8.5"></circle><path d="M12 7v5l3.2 2"></path><path d="M12 2.2v1.3M12 20.5v1.3M2.2 12h1.3M20.5 12h1.3"></path>',
  livros: '<rect x="3.5" y="4" width="4.2" height="16.5" rx=".6"></rect><rect x="7.7" y="6.5" width="4.2" height="14" rx=".6"></rect><path d="M13.4 7.3l3.9-1 3.6 13.6-3.9 1z"></path><path d="M3.5 7.5h4.2M7.7 9.5h4.2M3.5 17h4.2M7.7 17.5h4.2"></path>',
  ao_acordar: '<path d="M3 17.5h18M6.2 17.5a5.8 5.8 0 0 1 11.6 0"></path><path d="M12 5.2v2.3M5.4 8.4l1.6 1.6M18.6 8.4L17 10M2.8 13.6h1.8M19.4 13.6h1.8"></path><path d="M8 20.5h8"></path>',
  refeicoes: '<path d="M4 13.5c0-4.6 3.6-7.8 8-7.8s8 3.2 8 7.8v1.2c0 .9-.7 1.6-1.6 1.6H5.6c-.9 0-1.6-.7-1.6-1.6z"></path><path d="M8.6 9.2c.6 1 .9 2 .9 3.1M12 8.6c.4 1.2.6 2.4.6 3.7M15.4 9.2c-.6 1-.9 2-.9 3.1"></path><path d="M6 19.5h12"></path>',
  missa: '<circle cx="12" cy="3.6" r="1.9"></circle><path d="M6.4 7.4h11.2c0 3.4-2.5 5.6-5.6 5.6s-5.6-2.2-5.6-5.6z"></path><path d="M12 13v4.2M9.2 20.6c.3-2 1.4-3.4 2.8-3.4s2.5 1.4 2.8 3.4zM8 20.6h8"></path>',
  antes_de_dormir: '<path d="M19.5 14.6A8 8 0 0 1 9.4 4.5a8 8 0 1 0 10.1 10.1z"></path><path d="M16.4 4.2l.5 1.3 1.3.5-1.3.5-.5 1.3-.5-1.3-1.3-.5 1.3-.5z" stroke-width="1"></path>',
  lupa: '<circle cx="11" cy="11" r="6.5"></circle><path d="M20 20l-4.2-4.2"></path>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"></path>',
  fechar: '<path d="M6 6l12 12M18 6L6 18"></path>',
  esquerda: '<path d="M15 6l-6 6 6 6"></path>',
  direita: '<path d="M9 6l6 6-6 6"></path>',
  baixo: '<path d="M6 9l6 6 6-6"></path>',
  seta: '<path d="M5 12h14M13 6l6 6-6 6"></path>',
  alerta: '<circle cx="12" cy="12" r="8.5"></circle><path d="M12 7.5v5.5M12 16.2v.3"></path>',
  info: '<circle cx="12" cy="12" r="8.5"></circle><path d="M12 11v5.5M12 7.8v.3"></path>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"></path>',
  recarregar: '<path d="M19 12a7 7 0 1 1-2.05-4.95M19 4.5V9h-4.5"></path>',
  calendario: '<rect x="3.5" y="5" width="17" height="15.5" rx="1.8"></rect><path d="M3.5 9.8h17M8 3.2v3.6M16 3.2v3.6"></path>',
  limpar: '<path d="M4 7h16M9 7V4.5h6V7M6.5 7l1 13h9l1-13"></path>',
  dispositivo: '<rect x="6.5" y="2.8" width="11" height="18.4" rx="2"></rect><path d="M10.5 18h3"></path>',
};

export const Nomes_Dos_Icones = Object.keys(Desenhos_Dos_Icones);

// rotulo: quando o ícone tem significado sozinho, o leitor de tela lê o rótulo; senão fica escondido (aria-hidden)
export function icone(nome, { tamanho, rotulo, classe = "" } = {}) {
  const desenhoDoIcone = Desenhos_Dos_Icones[nome];
  if (!desenhoDoIcone) return "";
  const acessibilidade = rotulo ? `role="img" aria-label="${rotulo}"` : `aria-hidden="true" focusable="false"`;
  const classes = `fd-ico ${tamanho === 24 ? "fd-ico--24" : ""} ${classe}`.trim().replace(/\s+/g, " ");
  return `<svg class="${classes}" viewBox="0 0 24 24" ${acessibilidade}>${desenhoDoIcone}</svg>`;
}

/** Mantém o foco do teclado dentro de `container` (drawer, modal). */
const FOCAVEIS = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function prenderFoco(evento, container) {
  if (evento.key !== "Tab" || !container) return;
  const itens = [...container.querySelectorAll(FOCAVEIS)].filter((el) => el.offsetParent !== null || el === document.activeElement);
  if (itens.length === 0) return;
  const primeiro = itens[0];
  const ultimo = itens[itens.length - 1];
  if (evento.shiftKey && document.activeElement === primeiro) { evento.preventDefault(); ultimo.focus(); }
  else if (!evento.shiftKey && document.activeElement === ultimo) { evento.preventDefault(); primeiro.focus(); }
}

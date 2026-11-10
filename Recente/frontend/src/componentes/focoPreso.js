const Seletor_De_Elementos_Focaveis = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

// com Tab, o foco gira só dentro do menu/modal aberto (acessibilidade)
export function prenderFocoNoContainer(eventoDeTeclado, container) {
  if (eventoDeTeclado.key !== "Tab" || !container) return;
  const elementosFocaveis = [...container.querySelectorAll(Seletor_De_Elementos_Focaveis)]
    .filter((elemento) => elemento.offsetParent !== null || elemento === document.activeElement);
  if (elementosFocaveis.length === 0) return;
  const primeiroElemento = elementosFocaveis[0];
  const ultimoElemento = elementosFocaveis[elementosFocaveis.length - 1];
  if (eventoDeTeclado.shiftKey && document.activeElement === primeiroElemento) {
    eventoDeTeclado.preventDefault();
    ultimoElemento.focus();
  } else if (!eventoDeTeclado.shiftKey && document.activeElement === ultimoElemento) {
    eventoDeTeclado.preventDefault();
    primeiroElemento.focus();
  }
}

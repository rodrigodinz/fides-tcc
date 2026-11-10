import { useEffect } from "react";

// muda o título da aba do navegador conforme a página
export function useTitulo(tituloDaPagina) {
  useEffect(() => {
    document.title = tituloDaPagina ? `${tituloDaPagina} · Fides` : "Fides";
  }, [tituloDaPagina]);
}

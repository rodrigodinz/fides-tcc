import { useEffect } from "react";

/** Título da aba: "Seção · Fides". */
export function useTitulo(titulo) {
  useEffect(() => {
    document.title = titulo ? `${titulo} · Fides` : "Fides";
  }, [titulo]);
}

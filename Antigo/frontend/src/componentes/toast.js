import { createContext, useContext } from "react";

export const ContextoToast = createContext(() => {});
/** avisar(texto): retorno breve (toast) de uma ação local. */
export const useToast = () => useContext(ContextoToast);

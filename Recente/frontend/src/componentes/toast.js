import { createContext, useContext } from "react";

// Context: forma do React de compartilhar algo com vários componentes sem passar por props
export const ContextoToast = createContext(() => {});

export const useToast = () => useContext(ContextoToast);

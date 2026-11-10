import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "@fontsource/cormorant-garamond/latin-400.css";
import "@fontsource/cormorant-garamond/latin-400-italic.css";
import "@fontsource/cormorant-garamond/latin-600.css";
import "@fontsource/cormorant-garamond/latin-700.css";
import "@fontsource/antic/latin-400.css";
// estilos globais: cores e fontes (tokens), base, componentes e páginas
import "./estilos/tokens.css";
import "./estilos/base.css";
import "./estilos/componentes.css";
import "./estilos/paginas.css";
import App from "./App.jsx";

// Ponto de partida do React: pega a <div id="raiz"> do index.html e desenha o <App /> dentro dela.
// BrowserRouter faz a URL do navegador controlar qual página aparece.
createRoot(document.getElementById("raiz")).render(
  <StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <App />
    </BrowserRouter>
  </StrictMode>,
);

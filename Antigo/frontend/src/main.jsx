import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
// Fontes servidas pelo próprio site (SIL OFL), sem depender de CDN.
import "@fontsource/cormorant-garamond/latin-400.css";
import "@fontsource/cormorant-garamond/latin-400-italic.css";
import "@fontsource/cormorant-garamond/latin-600.css";
import "@fontsource/cormorant-garamond/latin-700.css";
import "@fontsource/antic/latin-400.css";
import "./estilos/tokens.css";
import "./estilos/base.css";
import "./estilos/componentes.css";
import "./estilos/paginas.css";
import App from "./App.jsx";

createRoot(document.getElementById("raiz")).render(
  <StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <App />
    </BrowserRouter>
  </StrictMode>,
);

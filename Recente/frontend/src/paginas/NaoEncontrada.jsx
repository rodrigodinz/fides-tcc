import { useTitulo } from "../hooks/useTitulo.js";
import { NaoEncontrado } from "../componentes/Estados.jsx";

// qualquer endereço que não existe cai aqui (rota "*" no App.jsx)
export default function NaoEncontrada() {
  useTitulo("Página não encontrada");
  return <div className="fd-container fd-pagina"><NaoEncontrado titulo="Página não encontrada" voltar={{ para: "/", texto: "Ir para o início" }} /></div>;
}

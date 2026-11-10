import { Route, Routes } from "react-router-dom";
import Layout from "./componentes/layout/Layout.jsx";
import { ProvedorToast } from "./componentes/Retorno.jsx";
import Inicio from "./paginas/Inicio.jsx";
import Santos from "./paginas/Santos.jsx";
import Santo from "./paginas/Santo.jsx";
import Oracoes from "./paginas/Oracoes.jsx";
import Novenas from "./paginas/Novenas.jsx";
import Novena from "./paginas/Novena.jsx";
import Livros from "./paginas/Livros.jsx";
import Livro from "./paginas/Livro.jsx";
import LiturgiaDia from "./paginas/LiturgiaDia.jsx";
import LiturgiaHoras from "./paginas/LiturgiaHoras.jsx";
import Agenda from "./paginas/Agenda.jsx";
import NaoEncontrada from "./paginas/NaoEncontrada.jsx";

// Mapa de rotas do site: cada <Route> liga um endereço (path) a uma página.
// Todas ficam dentro do <Layout>, que desenha a navbar, o menu e o rodapé em volta da página.
export default function App() {
  return (
    <ProvedorToast>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Inicio />} />
          <Route path="santos" element={<Santos />} />
          <Route path="santos/:id" element={<Santo />} />
          <Route path="oracoes" element={<Oracoes />} />
          <Route path="novenas" element={<Novenas />} />
          <Route path="novenas/:id" element={<Novena />} />
          <Route path="novenas/:id/dia/:numero" element={<Novena />} />
          <Route path="livros" element={<Livros />} />
          <Route path="livros/:id" element={<Livro />} />
          <Route path="liturgia" element={<LiturgiaDia />} />
          <Route path="liturgia/horas" element={<LiturgiaHoras />} />
          <Route path="agenda" element={<Agenda />} />
          {/* "*" pega qualquer endereço que não bateu com as rotas acima */}
          <Route path="*" element={<NaoEncontrada />} />
        </Route>
      </Routes>
    </ProvedorToast>
  );
}

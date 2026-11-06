import { Link, useParams } from "react-router-dom";
import { servicoLivros } from "../api/servicos.js";
import { ehErroDeNaoEncontrado } from "../api/erros.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { lerIdDaUrl } from "../utils/paginacao.js";
import { CabecalhoPagina, Migalhas } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import { Alerta, Carregando, EstadoErro, NaoEncontrado } from "../componentes/Estados.jsx";

// Detalhe do livro: autor, santo, resumo e contexto histórico.
export default function Livro() {
  const livroId = lerIdDaUrl(useParams().id);
  const consultaDoLivro = useConsulta(`livro:${livroId}`, (signal) => servicoLivros.detalharLivro(livroId, { signal }), { consultaAtiva: livroId !== null });
  const livro = consultaDoLivro.estado === "sucesso" ? consultaDoLivro.dados : null;
  useTitulo(livro?.titulo ?? "Livro");
  if (livroId === null || (consultaDoLivro.estado === "erro" && ehErroDeNaoEncontrado(consultaDoLivro.erro))) {
    return <div className="fd-container fd-pagina"><NaoEncontrado titulo="Livro não encontrado" voltar={{ para: "/livros", texto: "Voltar aos livros" }} /></div>;
  }
  return (
    <div className="fd-container fd-pagina">
      <Migalhas itens={[{ texto: "Início", para: "/" }, { texto: "Livros", para: "/livros" }, { texto: livro?.titulo ?? "Livro" }]} />
      {consultaDoLivro.estado === "carregando" && <Carregando tipo="texto" quantidade={5} texto="Carregando o livro…" />}
      {consultaDoLivro.estado === "erro" && <EstadoErro erro={consultaDoLivro.erro} conteudoBuscado="este livro" aoTentarNovamente={consultaDoLivro.recarregar} />}
      {livro && (
        <article>
          <CabecalhoPagina titulo={livro.titulo} rotulo="Livro">
            <p className="fd-livro-autor">{livro.autor}</p>
            {livro.santo && <p style={{ marginTop: 6, textAlign: "center" }}><Link className="fd-link fd-link--vinho" to={`/santos/${livro.santo.id}`}>{livro.santo.nome}</Link></p>}
          </CabecalhoPagina>
          <Ornamento tipo="divisor" />
          <div className="fd-blocos">
            {livro.resumo && (
              <section className="fd-bloco" aria-labelledby="resumo">
                <Ornamento tipo="curto" /><h2 id="resumo" className="fd-h3">Resumo</h2><p className="fd-texto-longo">{livro.resumo}</p>
              </section>
            )}
            {livro.contexto_historico && (
              <section className="fd-bloco" aria-labelledby="contexto">
                <Ornamento tipo="curto" /><h2 id="contexto" className="fd-h3">Contexto histórico</h2><p className="fd-texto-longo">{livro.contexto_historico}</p>
              </section>
            )}
            {!livro.resumo && !livro.contexto_historico && (
              <Alerta tipo="info" titulo="Sem resumo cadastrado">O resumo e o contexto histórico deste livro ainda não foram cadastrados.</Alerta>
            )}
          </div>
        </article>
      )}
    </div>
  );
}

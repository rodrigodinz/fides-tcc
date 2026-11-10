import { Link, useParams } from "react-router-dom";
import { livros as api } from "../api/servicos.js";
import { ehNaoEncontrado } from "../api/erros.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { lerId } from "../utils/paginacao.js";
import { CabecalhoPagina, Migalhas } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import { Alerta, Carregando, EstadoErro, NaoEncontrado } from "../componentes/Estados.jsx";

export default function Livro() {
  const id = lerId(useParams().id);
  const c = useConsulta(`livro:${id}`, (signal) => api.detalhar(id, { signal }), { ativo: id !== null });
  const livro = c.estado === "sucesso" ? c.dados : null;
  useTitulo(livro?.titulo ?? "Livro");
  if (id === null || (c.estado === "erro" && ehNaoEncontrado(c.erro))) {
    return <div className="fd-container fd-pagina"><NaoEncontrado titulo="Livro não encontrado" voltar={{ para: "/livros", texto: "Voltar aos livros" }} /></div>;
  }
  return (
    <div className="fd-container fd-pagina">
      <Migalhas itens={[{ texto: "Início", para: "/" }, { texto: "Livros", para: "/livros" }, { texto: livro?.titulo ?? "Livro" }]} />
      {c.estado === "carregando" && <Carregando tipo="texto" quantidade={5} texto="Carregando o livro…" />}
      {c.estado === "erro" && <EstadoErro erro={c.erro} oQue="este livro" aoTentar={c.recarregar} />}
      {livro && (
        <article>
          <CabecalhoPagina titulo={livro.titulo} rotulo="Livro">
            <p className="fd-livro-autor">{livro.autor}</p>
            {livro.santo && <p style={{ marginTop: 6, textAlign: "center" }}><Link className="fd-link fd-link--vinho" to={`/santos/${livro.santo.id}`}>{livro.santo.nome}</Link></p>}
          </CabecalhoPagina>
          <Ornamento tipo="divisor" />
          <div className="fd-blocos">
            {livro.resumo && (
              <section className="fd-bloco" aria-labelledby="resumo"><Ornamento tipo="curto" /><h2 id="resumo" className="fd-h3">Resumo</h2><p className="fd-texto-longo">{livro.resumo}</p></section>
            )}
            {livro.contexto_historico && (
              <section className="fd-bloco" aria-labelledby="contexto"><Ornamento tipo="curto" /><h2 id="contexto" className="fd-h3">Contexto histórico</h2><p className="fd-texto-longo">{livro.contexto_historico}</p></section>
            )}
            {!livro.resumo && !livro.contexto_historico && <Alerta tipo="info" titulo="Sem resumo cadastrado">O resumo e o contexto histórico deste livro ainda não foram cadastrados.</Alerta>}
          </div>
        </article>
      )}
    </div>
  );
}

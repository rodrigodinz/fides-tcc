import { Link, useSearchParams } from "react-router-dom";
import { servicoLivros, servicoSantos, listarTodasAsPaginas } from "../api/servicos.js";
import { paginaEstaVazia, useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { listarSantosAcessados } from "../estado/santosAcessados.js";
import { lerIdDaUrl, lerNumeroDaPagina } from "../utils/paginacao.js";
import { CabecalhoPagina, TituloSecao } from "../componentes/Estrutura.jsx";
import { Seletor } from "../componentes/Campos.jsx";
import Card from "../componentes/Card.jsx";
import Icone from "../componentes/Icone.jsx";
import Paginacao from "../componentes/Paginacao.jsx";
import { Botao, BotaoLink } from "../componentes/Botao.jsx";
import { Carregando, EstadoErro, EstadoVazio } from "../componentes/Estados.jsx";

const escreverAutoriaDoLivro = (livro) =>
  [livro.autor, livro.santo?.nome && livro.santo.nome !== livro.autor ? livro.santo.nome : null].filter(Boolean).join(" · ");

// recomendação de leitura: livros dos santos visitados neste aparelho (GET /livros/recomendados)
function LivrosRecomendados() {
  const idsDosSantosAcessados = listarSantosAcessados();
  const consultaDeRecomendados = useConsulta(`livros:recomendados:${idsDosSantosAcessados.join(",")}`,
    (signal) => servicoLivros.listarLivrosRecomendados(idsDosSantosAcessados, {}, { signal }),
    { consultaAtiva: idsDosSantosAcessados.length > 0, verificarSeVazio: paginaEstaVazia });

  let conteudoDaSecao;
  if (idsDosSantosAcessados.length === 0) {
    conteudoDaSecao = (
      <Card simples nivel={3} titulo="Ainda sem recomendações">
        <p className="fd-card__corpo-texto">Visite a página de um santo e os livros ligados a ele aparecerão aqui.</p>
        <div className="fd-card__acoes"><BotaoLink variante="secundario" icone="santos" to="/santos">Explorar santos</BotaoLink></div>
      </Card>
    );
  } else if (consultaDeRecomendados.estado === "carregando") {
    conteudoDaSecao = <Carregando quantidade={2} texto="Carregando recomendações…" />;
  } else if (consultaDeRecomendados.estado === "erro") {
    conteudoDaSecao = <EstadoErro erro={consultaDeRecomendados.erro} conteudoBuscado="as recomendações" aoTentarNovamente={consultaDeRecomendados.recarregar} />;
  } else if (consultaDeRecomendados.estado === "vazio") {
    conteudoDaSecao = <p className="fd-aux">Os santos que você visitou ainda não têm livros cadastrados. Veja o catálogo abaixo.</p>;
  } else {
    conteudoDaSecao = (
      <div className="fd-grade fd-grade--3">
        {consultaDeRecomendados.dados.itens.map((livro) => (
          <Card key={livro.id} destaque={false} titulo={livro.titulo} para={`/livros/${livro.id}`} meta={escreverAutoriaDoLivro(livro)} rotulo="Recomendação de leitura" />
        ))}
      </div>
    );
  }

  return (
    <section className="fd-secao" aria-labelledby="rec-titulo">
      <TituloSecao id="rec-titulo" titulo="Recomendados para você" descricao="Com base nos santos que você visitou neste dispositivo." />
      {conteudoDaSecao}
    </section>
  );
}

// Recomendações no topo e catálogo completo com filtro por santo e paginação.
export default function Livros() {
  useTitulo("Livros");
  const [parametrosDaUrl, setParametrosDaUrl] = useSearchParams();
  const santoFiltrado = lerIdDaUrl(parametrosDaUrl.get("santo"));
  const pagina = lerNumeroDaPagina(parametrosDaUrl.get("pagina"));
  const consultaDeSantos = useConsulta("santos:todos", (signal) =>
    listarTodasAsPaginas((filtros, opcoes) => servicoSantos.listarSantos(filtros, opcoes), {}, { signal }));
  const consultaDeLivros = useConsulta(`livros:${santoFiltrado}:${pagina}`,
    (signal) => servicoLivros.listarLivros({ pagina, santo_id: santoFiltrado ?? undefined }, { signal }), { verificarSeVazio: paginaEstaVazia });
  const filtrarPorSanto = (santoId) => {
    const novosParametros = new URLSearchParams();
    if (santoId) novosParametros.set("santo", santoId);
    setParametrosDaUrl(novosParametros, { replace: true });
  };
  const irParaPagina = (numeroDaPagina) => {
    const novosParametros = new URLSearchParams(parametrosDaUrl);
    novosParametros.set("pagina", String(numeroDaPagina));
    setParametrosDaUrl(novosParametros);
  };
  const opcoesDeSanto = consultaDeSantos.estado === "sucesso"
    ? consultaDeSantos.dados.map((santo) => ({ valor: santo.id, rotulo: santo.nome }))
    : [];

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Livros" textoDeAbertura="Obras dos santos e textos importantes da fé, com resumo e contexto histórico." />
      <LivrosRecomendados />
      <section className="fd-secao" aria-labelledby="cat-titulo">
        <TituloSecao id="cat-titulo" titulo="Catálogo" />
        <div className="fd-leitura" style={{ marginBottom: 24 }}>
          <Seletor rotulo="Filtrar por santo" valor={santoFiltrado ?? ""} aoMudar={filtrarPorSanto} textoDeTodos="Todos os livros"
            desabilitado={consultaDeSantos.estado !== "sucesso"} opcoes={opcoesDeSanto} />
        </div>
        {consultaDeLivros.estado === "carregando" && <Carregando quantidade={4} texto="Carregando livros…" />}
        {consultaDeLivros.estado === "erro" && <EstadoErro erro={consultaDeLivros.erro} conteudoBuscado="os livros" aoTentarNovamente={consultaDeLivros.recarregar} />}
        {consultaDeLivros.estado === "vazio" && (
          <EstadoVazio titulo="Nenhum livro encontrado" texto={santoFiltrado ? "Este santo ainda não tem livros cadastrados." : null}
            acao={santoFiltrado ? <Botao variante="secundario" icone="fechar" onClick={() => filtrarPorSanto("")}>Ver todos os livros</Botao> : null} />
        )}
        {consultaDeLivros.estado === "sucesso" && (
          <>
            <ul className="fd-lista fd-lista-rica">
              {consultaDeLivros.dados.itens.map((livro) => (
                <li key={livro.id}>
                  <div><Link className="fd-lista__titulo" to={`/livros/${livro.id}`}>{livro.titulo}</Link><p className="fd-aux">{escreverAutoriaDoLivro(livro)}</p></div>
                  <Icone nome="direita" />
                </li>
              ))}
            </ul>
            <Paginacao pagina={consultaDeLivros.dados.pagina} totalPaginas={consultaDeLivros.dados.total_paginas}
              totalRegistros={consultaDeLivros.dados.total_registros_filtros} aoMudarPagina={irParaPagina} rotulo="Páginas de livros" />
          </>
        )}
      </section>
    </div>
  );
}

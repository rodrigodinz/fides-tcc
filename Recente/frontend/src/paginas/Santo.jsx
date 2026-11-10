import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { servicoSantos, servicoOracoes, servicoNovenas } from "../api/servicos.js";
import { ehErroDeNaoEncontrado } from "../api/erros.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { registrarSantoAcessado } from "../estado/santosAcessados.js";
import { lerIdDaUrl } from "../utils/paginacao.js";
import { CabecalhoPagina, Migalhas, TituloSecao } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import RetratoSanto from "../componentes/RetratoSanto.jsx";
import CardNovena from "../componentes/CardNovena.jsx";
import CardOracao from "../componentes/CardOracao.jsx";
import Icone from "../componentes/Icone.jsx";
import { Carregando, EstadoErro, NaoEncontrado } from "../componentes/Estados.jsx";

function OracoesDoSanto({ santoId, totalDeOracoes }) {
  const consultaDeOracoes = useConsulta(`santo:${santoId}:oracoes`, (signal) => servicoOracoes.listarOracoes({ santo_id: santoId }, { signal }),
    { consultaAtiva: totalDeOracoes > 0 });
  if (totalDeOracoes === 0) return <p className="fd-aux">Nenhuma oração vinculada a este santo.</p>;
  if (consultaDeOracoes.estado === "carregando") return <Carregando quantidade={1} texto="Carregando orações…" />;
  if (consultaDeOracoes.estado === "erro") {
    return <EstadoErro erro={consultaDeOracoes.erro} conteudoBuscado="as orações deste santo" aoTentarNovamente={consultaDeOracoes.recarregar} />;
  }
  return <div className="fd-pilha-cards">{consultaDeOracoes.dados.itens.map((oracao) => <CardOracao key={oracao.id} oracao={oracao} />)}</div>;
}

function NovenasDoSanto({ santoId, totalDeNovenas }) {
  const consultaDeNovenas = useConsulta(`santo:${santoId}:novenas`, (signal) => servicoNovenas.listarNovenas({ santo_id: santoId }, { signal }),
    { consultaAtiva: totalDeNovenas > 0 });
  if (totalDeNovenas === 0) return <p className="fd-aux">Nenhuma novena vinculada a este santo.</p>;
  if (consultaDeNovenas.estado === "carregando") return <Carregando quantidade={1} texto="Carregando novenas…" />;
  if (consultaDeNovenas.estado === "erro") {
    return <EstadoErro erro={consultaDeNovenas.erro} conteudoBuscado="as novenas deste santo" aoTentarNovamente={consultaDeNovenas.recarregar} />;
  }
  return <div className="fd-pilha-cards">{consultaDeNovenas.dados.itens.map((novena) => <CardNovena key={novena.id} novena={novena} nivel={3} />)}</div>;
}

// Detalhe do santo: biografia, novenas, livros e orações.
// Ao abrir, o id é guardado em "santos acessados" para a recomendação de livros.
export default function Santo() {
  // useParams: pega o :id da rota /santos/:id
  const santoId = lerIdDaUrl(useParams().id);
  const consultaDoSanto = useConsulta(`santo:${santoId}`, (signal) => servicoSantos.detalharSanto(santoId, { signal }), { consultaAtiva: santoId !== null });
  const santo = consultaDoSanto.estado === "sucesso" ? consultaDoSanto.dados : null;
  useTitulo(santo?.nome ?? "Santo");

  // assim que o santo carrega, registra a visita no aparelho
  useEffect(() => { if (santo) registrarSantoAcessado(santo.id); }, [santo]);

  const voltarParaSantos = { para: "/santos", texto: "Voltar aos santos" };
  if (santoId === null || (consultaDoSanto.estado === "erro" && ehErroDeNaoEncontrado(consultaDoSanto.erro))) {
    return <div className="fd-container fd-pagina"><NaoEncontrado titulo="Santo não encontrado" voltar={voltarParaSantos} /></div>;
  }
  return (
    <div className="fd-container fd-pagina">
      <Migalhas itens={[{ texto: "Início", para: "/" }, { texto: "Santos", para: "/santos" }, { texto: santo?.nome ?? "Santo" }]} />
      {consultaDoSanto.estado === "carregando" && <Carregando tipo="texto" quantidade={5} texto="Carregando o santo…" />}
      {consultaDoSanto.estado === "erro" && <EstadoErro erro={consultaDoSanto.erro} conteudoBuscado="este santo" aoTentarNovamente={consultaDoSanto.recarregar} />}
      {santo && (
        <>
          <div className="fd-santo-topo">
            <div className="fd-moldura"><RetratoSanto fotoUrl={santo.foto_url} nome={santo.nome} carregamento="eager" /></div>
            <div>
              <CabecalhoPagina titulo={santo.nome} rotulo="Santos" />
              <div className="fd-leitura fd-santo-bio">
                {santo.biografia ? <p className="fd-texto-longo">{santo.biografia}</p> : <p className="fd-aux">Biografia ainda não cadastrada.</p>}
              </div>
            </div>
          </div>
          <Ornamento tipo="divisor" />
          <div className="fd-santo-secoes">
            <div>
              <section aria-labelledby="sec-novenas">
                <TituloSecao id="sec-novenas" titulo="Novenas" />
                <NovenasDoSanto santoId={santo.id} totalDeNovenas={santo.novenas.length} />
              </section>
              <section className="fd-secao" aria-labelledby="sec-livros">
                <TituloSecao id="sec-livros" titulo="Livros" />
                {santo.livros.length === 0 ? <p className="fd-aux">Nenhum livro vinculado a este santo.</p> : (
                  <ul className="fd-lista fd-lista-rica" aria-labelledby="sec-livros">
                    {santo.livros.map((livro) => (
                      <li key={livro.id}>
                        <div><Link className="fd-lista__titulo" to={`/livros/${livro.id}`}>{livro.titulo}</Link><p className="fd-aux">{livro.autor}</p></div>
                        <Icone nome="direita" />
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            </div>
            <section aria-labelledby="sec-oracoes">
              <TituloSecao id="sec-oracoes" titulo="Orações" />
              <OracoesDoSanto santoId={santo.id} totalDeOracoes={santo.oracoes.length} />
            </section>
          </div>
        </>
      )}
    </div>
  );
}

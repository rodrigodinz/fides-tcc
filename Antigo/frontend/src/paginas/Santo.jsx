import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { santos as apiSantos, oracoes as apiOracoes, novenas as apiNovenas } from "../api/servicos.js";
import { ehNaoEncontrado } from "../api/erros.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { registrarSantoAcessado } from "../estado/santosAcessados.js";
import { lerId } from "../utils/paginacao.js";
import { CabecalhoPagina, Migalhas, TituloSecao } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import RetratoSanto from "../componentes/RetratoSanto.jsx";
import CardNovena from "../componentes/CardNovena.jsx";
import CardOracao from "../componentes/CardOracao.jsx";
import Icone from "../componentes/Icone.jsx";
import { Carregando, EstadoErro, NaoEncontrado } from "../componentes/Estados.jsx";

/** Orações completas do santo vêm de /oracoes?santo_id= (o detalhe só traz títulos). */
function OracoesDoSanto({ santoId, total }) {
  const c = useConsulta(`santo:${santoId}:oracoes`, (signal) => apiOracoes.listar({ santo_id: santoId }, { signal }), { ativo: total > 0 });
  if (total === 0) return <p className="fd-aux">Nenhuma oração vinculada a este santo.</p>;
  if (c.estado === "carregando") return <Carregando quantidade={1} texto="Carregando orações…" />;
  if (c.estado === "erro") return <EstadoErro erro={c.erro} oQue="as orações deste santo" aoTentar={c.recarregar} />;
  return <div className="fd-pilha-cards">{c.dados.itens.map((o) => <CardOracao key={o.id} oracao={o} />)}</div>;
}

/** Novenas do santo com a situação da agenda (/novenas?santo_id=). */
function NovenasDoSanto({ santoId, total }) {
  const c = useConsulta(`santo:${santoId}:novenas`, (signal) => apiNovenas.listar({ santo_id: santoId }, { signal }), { ativo: total > 0 });
  if (total === 0) return <p className="fd-aux">Nenhuma novena vinculada a este santo.</p>;
  if (c.estado === "carregando") return <Carregando quantidade={1} texto="Carregando novenas…" />;
  if (c.estado === "erro") return <EstadoErro erro={c.erro} oQue="as novenas deste santo" aoTentar={c.recarregar} />;
  return <div className="fd-pilha-cards">{c.dados.itens.map((n) => <CardNovena key={n.id} novena={n} nivel={3} />)}</div>;
}

export default function Santo() {
  const id = lerId(useParams().id);
  const c = useConsulta(`santo:${id}`, (signal) => apiSantos.detalhar(id, { signal }), { ativo: id !== null });
  const santo = c.estado === "sucesso" ? c.dados : null;
  useTitulo(santo?.nome ?? "Santo");

  // Registra o acesso só quando o santo existe de fato (base da recomendação de livros).
  useEffect(() => { if (santo) registrarSantoAcessado(santo.id); }, [santo]);

  const voltar = { para: "/santos", texto: "Voltar aos santos" };
  if (id === null || (c.estado === "erro" && ehNaoEncontrado(c.erro))) {
    return <div className="fd-container fd-pagina"><NaoEncontrado titulo="Santo não encontrado" voltar={voltar} /></div>;
  }
  return (
    <div className="fd-container fd-pagina">
      <Migalhas itens={[{ texto: "Início", para: "/" }, { texto: "Santos", para: "/santos" }, { texto: santo?.nome ?? "Santo" }]} />
      {c.estado === "carregando" && <Carregando tipo="texto" quantidade={5} texto="Carregando o santo…" />}
      {c.estado === "erro" && <EstadoErro erro={c.erro} oQue="este santo" aoTentar={c.recarregar} />}
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
              <NovenasDoSanto santoId={santo.id} total={santo.novenas.length} />
            </section>
            <section className="fd-secao" aria-labelledby="sec-livros">
              <TituloSecao id="sec-livros" titulo="Livros" />
              {santo.livros.length === 0 ? <p className="fd-aux">Nenhum livro vinculado a este santo.</p> : (
                <ul className="fd-lista fd-lista-rica" aria-labelledby="sec-livros">
                  {santo.livros.map((l) => (
                    <li key={l.id}>
                      <div><Link className="fd-lista__titulo" to={`/livros/${l.id}`}>{l.titulo}</Link><p className="fd-aux">{l.autor}</p></div>
                      <Icone nome="direita" />
                    </li>
                  ))}
                </ul>
              )}
            </section>
            </div>
            <section aria-labelledby="sec-oracoes">
              <TituloSecao id="sec-oracoes" titulo="Orações" />
              <OracoesDoSanto santoId={santo.id} total={santo.oracoes.length} />
            </section>
          </div>
        </>
      )}
    </div>
  );
}

import { Link, useSearchParams } from "react-router-dom";
import { livros as api, santos as apiSantos, listarTudo } from "../api/servicos.js";
import { listaVazia, useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { listarSantosAcessados } from "../estado/santosAcessados.js";
import { lerId, lerPagina } from "../utils/paginacao.js";
import { CabecalhoPagina, TituloSecao } from "../componentes/Estrutura.jsx";
import { Seletor } from "../componentes/Campos.jsx";
import Card from "../componentes/Card.jsx";
import Icone from "../componentes/Icone.jsx";
import Paginacao from "../componentes/Paginacao.jsx";
import { Botao, BotaoLink } from "../componentes/Botao.jsx";
import { Carregando, EstadoErro, EstadoVazio } from "../componentes/Estados.jsx";

const autoria = (l) => [l.autor, l.santo?.nome && l.santo.nome !== l.autor ? l.santo.nome : null].filter(Boolean).join(" · ");

/** Recomendação pelos santos acessados neste dispositivo. Sem ids, a rota não é chamada (ela exige santo_id). */
function Recomendados() {
  const ids = listarSantosAcessados();
  const c = useConsulta(`livros:recomendados:${ids.join(",")}`, (signal) => api.recomendados(ids, {}, { signal }), { ativo: ids.length > 0, vazio: listaVazia });
  return (
    <section className="fd-secao" aria-labelledby="rec-titulo">
      <TituloSecao id="rec-titulo" titulo="Recomendados para você" descricao="Com base nos santos que você visitou neste dispositivo." />
      {ids.length === 0 ? (
        <Card simples nivel={3} titulo="Ainda sem recomendações">
          <p className="fd-card__corpo-texto">Visite a página de um santo e os livros ligados a ele aparecerão aqui.</p>
          <div className="fd-card__acoes"><BotaoLink variante="secundario" icone="santos" to="/santos">Explorar santos</BotaoLink></div>
        </Card>
      ) : c.estado === "carregando" ? <Carregando quantidade={2} texto="Carregando recomendações…" />
        : c.estado === "erro" ? <EstadoErro erro={c.erro} oQue="as recomendações" aoTentar={c.recarregar} />
        : c.estado === "vazio" ? <p className="fd-aux">Os santos que você visitou ainda não têm livros cadastrados. Veja o catálogo abaixo.</p>
        : <div className="fd-grade fd-grade--3">{c.dados.itens.map((l) => <Card key={l.id} destaque={false} titulo={l.titulo} para={`/livros/${l.id}`} meta={autoria(l)} rotulo="Recomendação de leitura" />)}</div>}
    </section>
  );
}

export default function Livros() {
  useTitulo("Livros");
  const [params, setParams] = useSearchParams();
  const santo = lerId(params.get("santo"));
  const pagina = lerPagina(params.get("pagina"));
  const santos = useConsulta("santos:todos", (signal) => listarTudo((f, o) => apiSantos.listar(f, o), {}, { signal }));
  const c = useConsulta(`livros:${santo}:${pagina}`, (signal) => api.listar({ pagina, santo_id: santo ?? undefined }, { signal }), { vazio: listaVazia });
  const definir = (v) => { const n = new URLSearchParams(); if (v) n.set("santo", v); setParams(n, { replace: true }); };
  const irPara = (p) => { const n = new URLSearchParams(params); n.set("pagina", String(p)); setParams(n); };

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Livros" lead="Obras dos santos e textos importantes da fé, com resumo e contexto histórico." />
      <Recomendados />
      <section className="fd-secao" aria-labelledby="cat-titulo">
        <TituloSecao id="cat-titulo" titulo="Catálogo" />
        <div className="fd-leitura" style={{ marginBottom: 24 }}>
          <Seletor rotulo="Filtrar por santo" valor={santo ?? ""} aoMudar={definir} todas="Todos os livros" desabilitado={santos.estado !== "sucesso"}
            opcoes={santos.estado === "sucesso" ? santos.dados.map((s) => ({ valor: s.id, rotulo: s.nome })) : []} />
        </div>
        {c.estado === "carregando" && <Carregando quantidade={4} texto="Carregando livros…" />}
        {c.estado === "erro" && <EstadoErro erro={c.erro} oQue="os livros" aoTentar={c.recarregar} />}
        {c.estado === "vazio" && <EstadoVazio titulo="Nenhum livro encontrado" texto={santo ? "Este santo ainda não tem livros cadastrados." : null}
          acao={santo ? <Botao variante="secundario" icone="fechar" onClick={() => definir("")}>Ver todos os livros</Botao> : null} />}
        {c.estado === "sucesso" && (
          <>
            <ul className="fd-lista fd-lista-rica">
              {c.dados.itens.map((l) => (
                <li key={l.id}>
                  <div><Link className="fd-lista__titulo" to={`/livros/${l.id}`}>{l.titulo}</Link><p className="fd-aux">{autoria(l)}</p></div>
                  <Icone nome="direita" />
                </li>
              ))}
            </ul>
            <Paginacao pagina={c.dados.pagina} totalPaginas={c.dados.total_paginas} total={c.dados.total} aoMudar={irPara} rotulo="Páginas de livros" />
          </>
        )}
      </section>
    </div>
  );
}

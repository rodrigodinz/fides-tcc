import { useSearchParams } from "react-router-dom";
import { novenas as api, santos as apiSantos, listarTudo } from "../api/servicos.js";
import { listaVazia, useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { lerId, lerPagina } from "../utils/paginacao.js";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import { Seletor } from "../componentes/Campos.jsx";
import CardNovena from "../componentes/CardNovena.jsx";
import Paginacao from "../componentes/Paginacao.jsx";
import { Botao } from "../componentes/Botao.jsx";
import { Carregando, EstadoErro, EstadoVazio } from "../componentes/Estados.jsx";

export default function Novenas() {
  useTitulo("Novenas");
  const [params, setParams] = useSearchParams();
  const santo = lerId(params.get("santo"));
  const pagina = lerPagina(params.get("pagina"));
  const santos = useConsulta("santos:todos", (signal) => listarTudo((f, o) => apiSantos.listar(f, o), {}, { signal }));
  const c = useConsulta(`novenas:${santo}:${pagina}`, (signal) => api.listar({ pagina, santo_id: santo ?? undefined }, { signal }), { vazio: listaVazia });
  const definir = (v) => { const n = new URLSearchParams(); if (v) n.set("santo", v); setParams(n, { replace: true }); };
  const irPara = (p) => { const n = new URLSearchParams(params); n.set("pagina", String(p)); setParams(n); };

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Novenas" lead="Nove dias de oração e reflexão. O dia de cada novena segue a agenda, igual para todos." />
      <div className="fd-leitura" style={{ margin: "32px auto 0" }}>
        <Seletor rotulo="Filtrar por santo" valor={santo ?? ""} aoMudar={definir} todas="Todos os santos" desabilitado={santos.estado !== "sucesso"}
          opcoes={santos.estado === "sucesso" ? santos.dados.map((s) => ({ valor: s.id, rotulo: s.nome })) : []} />
      </div>
      <section className="fd-secao" aria-label="Lista de novenas" aria-busy={c.estado === "carregando"}>
        {c.estado === "carregando" && <Carregando quantidade={4} texto="Carregando novenas…" />}
        {c.estado === "erro" && <EstadoErro erro={c.erro} oQue="as novenas" aoTentar={c.recarregar} />}
        {c.estado === "vazio" && <EstadoVazio titulo="Nenhuma novena encontrada" texto={santo ? "Este santo ainda não tem novenas cadastradas." : null}
          acao={santo ? <Botao variante="secundario" icone="fechar" onClick={() => definir("")}>Ver todas as novenas</Botao> : null} />}
        {c.estado === "sucesso" && (
          <>
            <div className="fd-grade fd-grade--2">{c.dados.itens.map((n) => <CardNovena key={n.id} novena={n} />)}</div>
            <Paginacao pagina={c.dados.pagina} totalPaginas={c.dados.total_paginas} total={c.dados.total} aoMudar={irPara} rotulo="Páginas de novenas" />
          </>
        )}
      </section>
    </div>
  );
}

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { santos as api } from "../api/servicos.js";
import { listaVazia, useConsulta } from "../hooks/useConsulta.js";
import { useAtraso } from "../hooks/useAtraso.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { lerPagina } from "../utils/paginacao.js";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import { CampoBusca } from "../componentes/Campos.jsx";
import CardSanto from "../componentes/CardSanto.jsx";
import Paginacao from "../componentes/Paginacao.jsx";
import { Botao } from "../componentes/Botao.jsx";
import { Carregando, EstadoErro, EstadoVazio } from "../componentes/Estados.jsx";

export default function Santos() {
  useTitulo("Santos");
  const [params, setParams] = useSearchParams();
  const q = params.get("q") ?? "";
  const pagina = lerPagina(params.get("pagina"));
  const [texto, setTexto] = useState(q);
  const textoAtrasado = useAtraso(texto);

  useEffect(() => { setTexto(q); }, [q]);
  useEffect(() => {
    if (textoAtrasado.trim() === q.trim()) return;
    const novo = new URLSearchParams(params);
    if (textoAtrasado.trim()) novo.set("q", textoAtrasado.trim()); else novo.delete("q");
    novo.delete("pagina");
    setParams(novo, { replace: true });
  }, [textoAtrasado]); // eslint-disable-line react-hooks/exhaustive-deps

  const c = useConsulta(`santos:${q}:${pagina}`, (signal) => api.listar({ q, pagina }, { signal }), { vazio: listaVazia });
  const irPara = (n) => { const novo = new URLSearchParams(params); novo.set("pagina", String(n)); setParams(novo); };

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Santos" lead="Conheça a vida de cada santo e as orações, novenas e livros ligados a ele." />
      <div className="fd-leitura" style={{ margin: "32px auto 0" }}>
        <CampoBusca rotulo="Buscar santo" valor={texto} aoMudar={setTexto} placeholder="Nome do santo, ex.: Tomás" ajuda="Acentos e maiúsculas não fazem diferença." />
      </div>
      <section className="fd-secao" aria-label="Resultados" aria-busy={c.estado === "carregando"}>
        {c.estado === "carregando" && <Carregando tipo="santos" quantidade={3} texto="Carregando santos…" />}
        {c.estado === "erro" && <EstadoErro erro={c.erro} oQue="os santos" aoTentar={c.recarregar} />}
        {c.estado === "vazio" && (
          <EstadoVazio titulo={q ? `Nenhum santo encontrado para “${q}”` : "Nenhum santo cadastrado"} texto={q ? "Confira a grafia ou veja todos os santos." : null}
            acao={q ? <Botao variante="secundario" icone="fechar" onClick={() => setTexto("")}>Limpar busca</Botao> : null} />
        )}
        {c.estado === "sucesso" && (
          <>
            <p className="fd-aux" role="status" style={{ marginBottom: 16 }}>{c.dados.total} {c.dados.total === 1 ? "santo" : "santos"}{q ? ` para “${q}”` : ""}</p>
            <div className="fd-grade fd-grade--3">{c.dados.itens.map((s) => <CardSanto key={s.id} santo={s} nivel={2} />)}</div>
            <Paginacao pagina={c.dados.pagina} totalPaginas={c.dados.total_paginas} total={c.dados.total} aoMudar={irPara} rotulo="Páginas de santos" />
          </>
        )}
      </section>
    </div>
  );
}

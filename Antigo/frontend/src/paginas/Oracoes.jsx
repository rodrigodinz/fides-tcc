import { useSearchParams } from "react-router-dom";
import { oracoes as api, santos as apiSantos, listarTudo } from "../api/servicos.js";
import { listaVazia, useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { lerId, lerPagina } from "../utils/paginacao.js";
import { NOMES_ICONES } from "../componentes/iconesDados.jsx";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import { Chips, Seletor } from "../componentes/Campos.jsx";
import Card from "../componentes/Card.jsx";
import CardOracao from "../componentes/CardOracao.jsx";
import Paginacao from "../componentes/Paginacao.jsx";
import { Botao } from "../componentes/Botao.jsx";
import { Alerta, Carregando, EstadoErro, EstadoVazio } from "../componentes/Estados.jsx";

const TIPOS = [{ valor: "basicas", rotulo: "Só orações básicas" }, { valor: "outras", rotulo: "Demais orações" }];

export default function Oracoes() {
  useTitulo("Orações");
  const [params, setParams] = useSearchParams();
  const momento = lerId(params.get("momento"));
  const santo = lerId(params.get("santo"));
  const tipo = ["basicas", "outras"].includes(params.get("tipo")) ? params.get("tipo") : "";
  const pagina = lerPagina(params.get("pagina"));
  const basica = tipo === "basicas" ? true : tipo === "outras" ? false : undefined;
  const temFiltro = Boolean(momento || santo || tipo);

  const momentos = useConsulta("momentos", (signal) => api.momentos({ signal }));
  const santos = useConsulta("santos:todos", (signal) => listarTudo((f, o) => apiSantos.listar(f, o), {}, { signal }));
  const c = useConsulta(`oracoes:${momento}:${santo}:${tipo}:${pagina}`,
    (signal) => api.listar({ pagina, basica, momento_id: momento ?? undefined, santo_id: santo ?? undefined }, { signal }), { vazio: listaVazia });

  // Mudar um filtro volta à página 1; filtros combinam (E lógico), como na API.
  const definir = (chave, valor) => {
    const novo = new URLSearchParams(params);
    if (valor) novo.set(chave, valor); else novo.delete(chave);
    novo.delete("pagina");
    setParams(novo, { replace: true });
  };
  const limpar = () => setParams(new URLSearchParams(), { replace: true });
  const irPara = (n) => { const novo = new URLSearchParams(params); novo.set("pagina", String(n)); setParams(novo); };

  const opcoesMomento = momentos.estado === "sucesso"
    ? momentos.dados.map((m) => ({ valor: m.id, rotulo: m.nome, icone: NOMES_ICONES.includes(m.codigo) ? m.codigo : undefined })) : [];
  const opcoesSanto = santos.estado === "sucesso" ? santos.dados.map((s) => ({ valor: s.id, rotulo: s.nome })) : [];

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Orações" lead="Orações para cada momento do dia, para rezar e ler por inteiro." />

      {tipo !== "basicas" && !temFiltro && (
        <div className="fd-secao">
          <Card destaque titulo="Orações básicas" rotulo="Para começar" nivel={2}
            acoes={<Botao variante="primario" onClick={() => definir("tipo", "basicas")}>Ver orações básicas</Botao>}>
            <p className="fd-card__corpo-texto">As orações mais conhecidas e rezadas, reunidas em um só lugar.</p>
          </Card>
        </div>
      )}

      <section className="fd-secao" aria-labelledby="filtros-titulo">
        <h2 id="filtros-titulo" className="fd-sr">Filtros</h2>
        {momentos.estado === "erro"
          ? <EstadoErro erro={momentos.erro} oQue="os momentos do dia" aoTentar={momentos.recarregar} />
          : <Chips rotulo="Momento do dia" valor={momento ?? ""} aoMudar={(v) => definir("momento", v)} opcoes={opcoesMomento} />}
        <div className="fd-filtros" style={{ marginTop: 20 }}>
          <Seletor rotulo="Santo" valor={santo ?? ""} aoMudar={(v) => definir("santo", v)} opcoes={opcoesSanto} todas="Todos os santos" desabilitado={santos.estado !== "sucesso"} />
          <Seletor rotulo="Tipo" valor={tipo} aoMudar={(v) => definir("tipo", v)} opcoes={TIPOS} todas="Todas as orações" />
        </div>
        {santos.estado === "erro" && <div style={{ marginTop: 12 }}><Alerta tipo="info" titulo="Filtro por santo indisponível">Não foi possível carregar a lista de santos agora.</Alerta></div>}
        <div className="fd-filtros__rodape">
          <p className="fd-aux" role="status">
            {c.estado === "sucesso" ? `${c.dados.total} ${c.dados.total === 1 ? "oração" : "orações"}` : c.estado === "vazio" ? "Nenhuma oração" : " "}
          </p>
          {temFiltro && <Botao variante="secundario" pequeno icone="fechar" onClick={limpar}>Limpar filtros</Botao>}
        </div>
      </section>

      <section className="fd-secao" style={{ marginTop: 24 }} aria-label="Lista de orações" aria-busy={c.estado === "carregando"}>
        {c.estado === "carregando" && <Carregando quantidade={4} texto="Carregando orações…" />}
        {c.estado === "erro" && <EstadoErro erro={c.erro} oQue="as orações" aoTentar={c.recarregar} />}
        {c.estado === "vazio" && <EstadoVazio titulo="Nenhuma oração com esses filtros" texto="Experimente outro momento do dia ou outro santo."
          acao={temFiltro ? <Botao variante="secundario" icone="fechar" onClick={limpar}>Limpar filtros</Botao> : null} />}
        {c.estado === "sucesso" && (
          <>
            <div className="fd-grade-oracoes">{c.dados.itens.map((o) => <CardOracao key={o.id} oracao={o} nivel={2} />)}</div>
            <Paginacao pagina={c.dados.pagina} totalPaginas={c.dados.total_paginas} total={c.dados.total} aoMudar={irPara} rotulo="Páginas de orações" />
          </>
        )}
      </section>
    </div>
  );
}

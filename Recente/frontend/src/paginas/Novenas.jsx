import { useSearchParams } from "react-router-dom";
import { servicoNovenas, servicoSantos, listarTodasAsPaginas } from "../api/servicos.js";
import { paginaEstaVazia, useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { lerIdDaUrl, lerNumeroDaPagina } from "../utils/paginacao.js";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import { Seletor } from "../componentes/Campos.jsx";
import CardNovena from "../componentes/CardNovena.jsx";
import Paginacao from "../componentes/Paginacao.jsx";
import { Botao } from "../componentes/Botao.jsx";
import { Carregando, EstadoErro, EstadoVazio } from "../componentes/Estados.jsx";

// Catálogo de novenas com filtro por santo; cada card mostra a situação da agenda.
export default function Novenas() {
  useTitulo("Novenas");
  const [parametrosDaUrl, setParametrosDaUrl] = useSearchParams();
  const santoFiltrado = lerIdDaUrl(parametrosDaUrl.get("santo"));
  const pagina = lerNumeroDaPagina(parametrosDaUrl.get("pagina"));
  const consultaDeSantos = useConsulta("santos:todos", (signal) =>
    listarTodasAsPaginas((filtros, opcoes) => servicoSantos.listarSantos(filtros, opcoes), {}, { signal }));
  const consultaDeNovenas = useConsulta(`novenas:${santoFiltrado}:${pagina}`,
    (signal) => servicoNovenas.listarNovenas({ pagina, santo_id: santoFiltrado ?? undefined }, { signal }), { verificarSeVazio: paginaEstaVazia });
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
      <CabecalhoPagina titulo="Novenas" textoDeAbertura="Nove dias de oração e reflexão. O dia de cada novena segue a agenda, igual para todos." />
      <div className="fd-leitura" style={{ margin: "32px auto 0" }}>
        <Seletor rotulo="Filtrar por santo" valor={santoFiltrado ?? ""} aoMudar={filtrarPorSanto} textoDeTodos="Todos os santos"
          desabilitado={consultaDeSantos.estado !== "sucesso"} opcoes={opcoesDeSanto} />
      </div>
      <section className="fd-secao" aria-label="Lista de novenas" aria-busy={consultaDeNovenas.estado === "carregando"}>
        {consultaDeNovenas.estado === "carregando" && <Carregando quantidade={4} texto="Carregando novenas…" />}
        {consultaDeNovenas.estado === "erro" && <EstadoErro erro={consultaDeNovenas.erro} conteudoBuscado="as novenas" aoTentarNovamente={consultaDeNovenas.recarregar} />}
        {consultaDeNovenas.estado === "vazio" && (
          <EstadoVazio titulo="Nenhuma novena encontrada" texto={santoFiltrado ? "Este santo ainda não tem novenas cadastradas." : null}
            acao={santoFiltrado ? <Botao variante="secundario" icone="fechar" onClick={() => filtrarPorSanto("")}>Ver todas as novenas</Botao> : null} />
        )}
        {consultaDeNovenas.estado === "sucesso" && (
          <>
            <div className="fd-grade fd-grade--2">{consultaDeNovenas.dados.itens.map((novena) => <CardNovena key={novena.id} novena={novena} />)}</div>
            <Paginacao pagina={consultaDeNovenas.dados.pagina} totalPaginas={consultaDeNovenas.dados.total_paginas}
              totalRegistros={consultaDeNovenas.dados.total_registros_filtros} aoMudarPagina={irParaPagina} rotulo="Páginas de novenas" />
          </>
        )}
      </section>
    </div>
  );
}

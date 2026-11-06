import { useSearchParams } from "react-router-dom";
import { servicoOracoes, servicoSantos, listarTodasAsPaginas } from "../api/servicos.js";
import { paginaEstaVazia, useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { lerIdDaUrl, lerNumeroDaPagina } from "../utils/paginacao.js";
import { Nomes_Dos_Icones } from "../componentes/iconesDados.jsx";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import { Chips, Seletor } from "../componentes/Campos.jsx";
import Card from "../componentes/Card.jsx";
import CardOracao from "../componentes/CardOracao.jsx";
import Paginacao from "../componentes/Paginacao.jsx";
import { Botao } from "../componentes/Botao.jsx";
import { Alerta, Carregando, EstadoErro, EstadoVazio } from "../componentes/Estados.jsx";

const Tipos_De_Oracao = [{ valor: "basicas", rotulo: "Só orações básicas" }, { valor: "outras", rotulo: "Demais orações" }];

// Orações com filtros combináveis (momento do dia, santo, tipo). Todos os filtros ficam na URL.
export default function Oracoes() {
  useTitulo("Orações");
  const [parametrosDaUrl, setParametrosDaUrl] = useSearchParams();
  const momentoFiltrado = lerIdDaUrl(parametrosDaUrl.get("momento"));
  const santoFiltrado = lerIdDaUrl(parametrosDaUrl.get("santo"));
  const tipoFiltrado = ["basicas", "outras"].includes(parametrosDaUrl.get("tipo")) ? parametrosDaUrl.get("tipo") : "";
  const pagina = lerNumeroDaPagina(parametrosDaUrl.get("pagina"));
  const filtroBasica = tipoFiltrado === "basicas" ? true : tipoFiltrado === "outras" ? false : undefined;
  const temFiltroAtivo = Boolean(momentoFiltrado || santoFiltrado || tipoFiltrado);

  const consultaDeMomentos = useConsulta("momentos", (signal) => servicoOracoes.listarMomentosDoDia({ signal }));
  const consultaDeSantos = useConsulta("santos:todos", (signal) =>
    listarTodasAsPaginas((filtros, opcoes) => servicoSantos.listarSantos(filtros, opcoes), {}, { signal }));
  const consultaDeOracoes = useConsulta(`oracoes:${momentoFiltrado}:${santoFiltrado}:${tipoFiltrado}:${pagina}`,
    (signal) => servicoOracoes.listarOracoes(
      { pagina, basica: filtroBasica, momento_id: momentoFiltrado ?? undefined, santo_id: santoFiltrado ?? undefined }, { signal }),
    { verificarSeVazio: paginaEstaVazia });

  // trocar filtro volta para a página 1
  const definirFiltro = (nomeDoFiltro, valorDoFiltro) => {
    const novosParametros = new URLSearchParams(parametrosDaUrl);
    if (valorDoFiltro) novosParametros.set(nomeDoFiltro, valorDoFiltro); else novosParametros.delete(nomeDoFiltro);
    novosParametros.delete("pagina");
    setParametrosDaUrl(novosParametros, { replace: true });
  };
  const limparFiltros = () => setParametrosDaUrl(new URLSearchParams(), { replace: true });
  const irParaPagina = (numeroDaPagina) => {
    const novosParametros = new URLSearchParams(parametrosDaUrl);
    novosParametros.set("pagina", String(numeroDaPagina));
    setParametrosDaUrl(novosParametros);
  };

  const opcoesDeMomento = consultaDeMomentos.estado === "sucesso"
    ? consultaDeMomentos.dados.map((momento) => ({ valor: momento.id, rotulo: momento.nome, icone: Nomes_Dos_Icones.includes(momento.codigo) ? momento.codigo : undefined }))
    : [];
  const opcoesDeSanto = consultaDeSantos.estado === "sucesso"
    ? consultaDeSantos.dados.map((santo) => ({ valor: santo.id, rotulo: santo.nome }))
    : [];
  const totalDeOracoes = consultaDeOracoes.dados?.total_registros_filtros;

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Orações" textoDeAbertura="Orações para cada momento do dia, para rezar e ler por inteiro." />

      {tipoFiltrado !== "basicas" && !temFiltroAtivo && (
        <div className="fd-secao">
          <Card destaque titulo="Orações básicas" rotulo="Para começar" nivel={2}
            acoes={<Botao variante="primario" onClick={() => definirFiltro("tipo", "basicas")}>Ver orações básicas</Botao>}>
            <p className="fd-card__corpo-texto">As orações mais conhecidas e rezadas, reunidas em um só lugar.</p>
          </Card>
        </div>
      )}

      <section className="fd-secao" aria-labelledby="filtros-titulo">
        <h2 id="filtros-titulo" className="fd-sr">Filtros</h2>
        {consultaDeMomentos.estado === "erro"
          ? <EstadoErro erro={consultaDeMomentos.erro} conteudoBuscado="os momentos do dia" aoTentarNovamente={consultaDeMomentos.recarregar} />
          : <Chips rotulo="Momento do dia" valor={momentoFiltrado ?? ""} aoMudar={(momentoId) => definirFiltro("momento", momentoId)} opcoes={opcoesDeMomento} />}
        <div className="fd-filtros" style={{ marginTop: 20 }}>
          <Seletor rotulo="Santo" valor={santoFiltrado ?? ""} aoMudar={(santoId) => definirFiltro("santo", santoId)} opcoes={opcoesDeSanto}
            textoDeTodos="Todos os santos" desabilitado={consultaDeSantos.estado !== "sucesso"} />
          <Seletor rotulo="Tipo" valor={tipoFiltrado} aoMudar={(tipo) => definirFiltro("tipo", tipo)} opcoes={Tipos_De_Oracao} textoDeTodos="Todas as orações" />
        </div>
        {consultaDeSantos.estado === "erro" && (
          <div style={{ marginTop: 12 }}><Alerta tipo="info" titulo="Filtro por santo indisponível">Não foi possível carregar a lista de santos agora.</Alerta></div>
        )}
        <div className="fd-filtros__rodape">
          <p className="fd-aux" role="status">
            {consultaDeOracoes.estado === "sucesso"
              ? `${totalDeOracoes} ${totalDeOracoes === 1 ? "oração" : "orações"}`
              : consultaDeOracoes.estado === "vazio" ? "Nenhuma oração" : " "}
          </p>
          {temFiltroAtivo && <Botao variante="secundario" pequeno icone="fechar" onClick={limparFiltros}>Limpar filtros</Botao>}
        </div>
      </section>

      <section className="fd-secao" style={{ marginTop: 24 }} aria-label="Lista de orações" aria-busy={consultaDeOracoes.estado === "carregando"}>
        {consultaDeOracoes.estado === "carregando" && <Carregando quantidade={4} texto="Carregando orações…" />}
        {consultaDeOracoes.estado === "erro" && <EstadoErro erro={consultaDeOracoes.erro} conteudoBuscado="as orações" aoTentarNovamente={consultaDeOracoes.recarregar} />}
        {consultaDeOracoes.estado === "vazio" && (
          <EstadoVazio titulo="Nenhuma oração com esses filtros" texto="Experimente outro momento do dia ou outro santo."
            acao={temFiltroAtivo ? <Botao variante="secundario" icone="fechar" onClick={limparFiltros}>Limpar filtros</Botao> : null} />
        )}
        {consultaDeOracoes.estado === "sucesso" && (
          <>
            <div className="fd-grade-oracoes">{consultaDeOracoes.dados.itens.map((oracao) => <CardOracao key={oracao.id} oracao={oracao} nivel={2} />)}</div>
            <Paginacao pagina={consultaDeOracoes.dados.pagina} totalPaginas={consultaDeOracoes.dados.total_paginas}
              totalRegistros={totalDeOracoes} aoMudarPagina={irParaPagina} rotulo="Páginas de orações" />
          </>
        )}
      </section>
    </div>
  );
}

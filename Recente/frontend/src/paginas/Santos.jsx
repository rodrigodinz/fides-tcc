import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { servicoSantos } from "../api/servicos.js";
import { paginaEstaVazia, useConsulta } from "../hooks/useConsulta.js";
import { useAtraso } from "../hooks/useAtraso.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { lerNumeroDaPagina } from "../utils/paginacao.js";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import { CampoBusca } from "../componentes/Campos.jsx";
import CardSanto from "../componentes/CardSanto.jsx";
import Paginacao from "../componentes/Paginacao.jsx";
import { Botao } from "../componentes/Botao.jsx";
import { Carregando, EstadoErro, EstadoVazio } from "../componentes/Estados.jsx";

// Lista e busca de santos. O texto buscado fica na URL (?nome=), então voltar no navegador
// mantém a busca. A busca só dispara 350 ms depois que a pessoa para de digitar.
export default function Santos() {
  useTitulo("Santos");
  // useSearchParams: lê e altera os parâmetros da URL (?nome=...&pagina=...)
  const [parametrosDaUrl, setParametrosDaUrl] = useSearchParams();
  const nomeBuscado = parametrosDaUrl.get("nome") ?? "";
  const pagina = lerNumeroDaPagina(parametrosDaUrl.get("pagina"));
  const [textoDigitado, setTextoDigitado] = useState(nomeBuscado);
  const textoDigitadoComAtraso = useAtraso(textoDigitado);

  useEffect(() => { setTextoDigitado(nomeBuscado); }, [nomeBuscado]);
  useEffect(() => {
    if (textoDigitadoComAtraso.trim() === nomeBuscado.trim()) return;
    const novosParametros = new URLSearchParams(parametrosDaUrl);
    if (textoDigitadoComAtraso.trim()) novosParametros.set("nome", textoDigitadoComAtraso.trim()); else novosParametros.delete("nome");
    novosParametros.delete("pagina");
    setParametrosDaUrl(novosParametros, { replace: true });
  }, [textoDigitadoComAtraso]); // eslint-disable-line react-hooks/exhaustive-deps

  // a chave inclui nome e página: mudou qualquer um, busca de novo
  const consultaDeSantos = useConsulta(`santos:${nomeBuscado}:${pagina}`, (signal) => servicoSantos.listarSantos({ nome: nomeBuscado, pagina }, { signal }),
    { verificarSeVazio: paginaEstaVazia });
  const irParaPagina = (numeroDaPagina) => {
    const novosParametros = new URLSearchParams(parametrosDaUrl);
    novosParametros.set("pagina", String(numeroDaPagina));
    setParametrosDaUrl(novosParametros);
  };
  const totalDeSantos = consultaDeSantos.dados?.total_registros_filtros;

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Santos" textoDeAbertura="Conheça a vida de cada santo e as orações, novenas e livros ligados a ele." />
      <div className="fd-leitura" style={{ margin: "32px auto 0" }}>
        <CampoBusca rotulo="Buscar santo" valor={textoDigitado} aoMudar={setTextoDigitado} placeholder="Nome do santo, ex.: Tomás" ajuda="Acentos e maiúsculas não fazem diferença." />
      </div>
      <section className="fd-secao" aria-label="Resultados" aria-busy={consultaDeSantos.estado === "carregando"}>
        {/* condição && <Componente />: só desenha o componente quando a condição é verdadeira */}
        {/* cada estado da consulta mostra uma coisa: carregando, erro, vazio ou a lista */}
        {consultaDeSantos.estado === "carregando" && <Carregando tipo="santos" quantidade={3} texto="Carregando santos…" />}
        {consultaDeSantos.estado === "erro" && <EstadoErro erro={consultaDeSantos.erro} conteudoBuscado="os santos" aoTentarNovamente={consultaDeSantos.recarregar} />}
        {consultaDeSantos.estado === "vazio" && (
          <EstadoVazio titulo={nomeBuscado ? `Nenhum santo encontrado para “${nomeBuscado}”` : "Nenhum santo cadastrado"}
            texto={nomeBuscado ? "Confira a grafia ou veja todos os santos." : null}
            acao={nomeBuscado ? <Botao variante="secundario" icone="fechar" onClick={() => setTextoDigitado("")}>Limpar busca</Botao> : null} />
        )}
        {consultaDeSantos.estado === "sucesso" && (
          <>
            <p className="fd-aux" role="status" style={{ marginBottom: 16 }}>
              {totalDeSantos} {totalDeSantos === 1 ? "santo" : "santos"}{nomeBuscado ? ` para “${nomeBuscado}”` : ""}
            </p>
            <div className="fd-grade fd-grade--3">{consultaDeSantos.dados.itens.map((santo) => <CardSanto key={santo.id} santo={santo} nivel={2} />)}</div>
            <Paginacao pagina={consultaDeSantos.dados.pagina} totalPaginas={consultaDeSantos.dados.total_paginas}
              totalRegistros={totalDeSantos} aoMudarPagina={irParaPagina} rotulo="Páginas de santos" />
          </>
        )}
      </section>
    </div>
  );
}

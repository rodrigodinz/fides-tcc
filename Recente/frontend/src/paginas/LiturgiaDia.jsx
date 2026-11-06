import { servicoLiturgia } from "../api/servicos.js";
import { ErroDaApi } from "../api/cliente.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useDataNaUrl } from "../hooks/useDataNaUrl.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { periodoConhecido, lembrarPeriodo } from "../utils/periodo.js";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import SeletorData from "../componentes/SeletorData.jsx";
import { AbasLiturgia, AvisoDemonstracao, ErroDeData } from "../componentes/Liturgia.jsx";
import { Carregando } from "../componentes/Estados.jsx";

function BlocoDeLeitura({ rotulo, texto, ehCitacao }) {
  return (
    <section className="fd-bloco">
      <Ornamento tipo="curto" />
      <h2 className="fd-h3">{rotulo}</h2>
      <p className={`fd-texto-longo${ehCitacao ? " fd-citacao" : ""}`}>{texto}</p>
    </section>
  );
}

// Liturgia do Dia. A Segunda Leitura só aparece quando existe (domingos e solenidades).
// O aviso de demonstração vem da própria API.
export default function LiturgiaDia() {
  useTitulo("Liturgia do Dia");
  const { data, dataInvalida, definirData } = useDataNaUrl();
  const consultaDaLiturgia = useConsulta(`liturgia:dia:${data ?? "hoje"}:${dataInvalida}`, (signal) => {
    if (dataInvalida) return Promise.reject(new ErroDaApi({ codigo: "PARAMETRO_INVALIDO", mensagem: "Data inválida." }));
    return servicoLiturgia.verLiturgiaDoDia(data, { signal }).then((liturgia) => { lembrarPeriodo(liturgia.periodo); return liturgia; });
  });
  const liturgiaDoDia = consultaDaLiturgia.estado === "sucesso" ? consultaDaLiturgia.dados : null;
  const periodo = liturgiaDoDia?.periodo ?? periodoConhecido();
  const dataExibida = liturgiaDoDia?.data ?? data ?? periodo?.hoje;
  const semLeituras = liturgiaDoDia && !liturgiaDoDia.primeira_leitura && !liturgiaDoDia.salmo && !liturgiaDoDia.evangelho && !liturgiaDoDia.segunda_leitura;

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Liturgia do Dia" rotulo={dataExibida ? escreverDataPorExtenso(dataExibida) : "Liturgia"} textoDeAbertura={liturgiaDoDia?.santo_celebrado || null} />
      <AbasLiturgia data={data} />
      {periodo && dataExibida && <SeletorData data={dataExibida} periodo={periodo} aoMudarData={(dataEscolhida) => definirData(dataEscolhida, periodo)} />}
      <div className="fd-blocos">
        {consultaDaLiturgia.estado === "carregando" && <Carregando tipo="texto" quantidade={6} texto="Carregando a liturgia…" />}
        {consultaDaLiturgia.estado === "erro" && <ErroDeData erro={consultaDaLiturgia.erro} aoVoltarParaHoje={() => definirData(undefined)} aoTentarNovamente={consultaDaLiturgia.recarregar} />}
        {liturgiaDoDia && (
          <>
            <AvisoDemonstracao texto={liturgiaDoDia.aviso} />
            {liturgiaDoDia.primeira_leitura && <BlocoDeLeitura rotulo="Primeira Leitura" texto={liturgiaDoDia.primeira_leitura} />}
            {liturgiaDoDia.salmo && <BlocoDeLeitura rotulo="Salmo Responsorial" texto={liturgiaDoDia.salmo} ehCitacao />}
            {liturgiaDoDia.segunda_leitura && <BlocoDeLeitura rotulo="Segunda Leitura" texto={liturgiaDoDia.segunda_leitura} />}
            {liturgiaDoDia.evangelho && <BlocoDeLeitura rotulo="Evangelho" texto={liturgiaDoDia.evangelho} />}
            {semLeituras && <p className="fd-aux">As leituras desta data não foram cadastradas.</p>}
          </>
        )}
      </div>
    </div>
  );
}

import { servicoLiturgia } from "../api/servicos.js";
import { ErroDaApi } from "../api/cliente.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useDataNaUrl } from "../hooks/useDataNaUrl.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { periodoConhecido, lembrarPeriodo } from "../utils/periodo.js";
import { ordenarHorasDaLiturgia } from "../utils/liturgia.js";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import SeletorData from "../componentes/SeletorData.jsx";
import { AbasLiturgia, AvisoDemonstracao, ErroDeData } from "../componentes/Liturgia.jsx";
import { Carregando, EstadoVazio } from "../componentes/Estados.jsx";

// Liturgia das Horas: Laudes, Horas médias e Vésperas da data escolhida.
export default function LiturgiaHoras() {
  useTitulo("Liturgia das Horas");
  const { data, dataInvalida, definirData } = useDataNaUrl();
  const consultaDasHoras = useConsulta(`liturgia:horas:${data ?? "hoje"}:${dataInvalida}`, (signal) => {
    if (dataInvalida) return Promise.reject(new ErroDaApi({ codigo: "PARAMETRO_INVALIDO", mensagem: "Data inválida." }));
    return servicoLiturgia.verLiturgiaDasHoras(data, undefined, { signal }).then((liturgia) => { lembrarPeriodo(liturgia.periodo); return liturgia; });
  }, { verificarSeVazio: (liturgia) => liturgia.horas.length === 0 });
  const liturgiaDasHoras = consultaDasHoras.dados;
  const periodo = liturgiaDasHoras?.periodo ?? periodoConhecido();
  const dataExibida = liturgiaDasHoras?.data ?? data ?? periodo?.hoje;

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Liturgia das Horas" rotulo={dataExibida ? escreverDataPorExtenso(dataExibida) : "Liturgia"} textoDeAbertura="Laudes, Horas médias e Vésperas." />
      <AbasLiturgia data={data} />
      {periodo && dataExibida && <SeletorData data={dataExibida} periodo={periodo} aoMudarData={(dataEscolhida) => definirData(dataEscolhida, periodo)} />}
      <div className="fd-blocos">
        {consultaDasHoras.estado === "carregando" && <Carregando tipo="texto" quantidade={6} texto="Carregando a Liturgia das Horas…" />}
        {consultaDasHoras.estado === "erro" && <ErroDeData erro={consultaDasHoras.erro} aoVoltarParaHoje={() => definirData(undefined)} aoTentarNovamente={consultaDasHoras.recarregar} />}
        {consultaDasHoras.estado === "vazio" && (
          <>
            <AvisoDemonstracao texto={liturgiaDasHoras.aviso} />
            <EstadoVazio titulo="Sem Liturgia das Horas para esta data" texto="Escolha outra data no período disponível." />
          </>
        )}
        {consultaDasHoras.estado === "sucesso" && (
          <>
            <AvisoDemonstracao texto={liturgiaDasHoras.aviso} />
            {ordenarHorasDaLiturgia(liturgiaDasHoras.horas).map((hora) => (
              <section key={hora.bloco.codigo} className="fd-bloco" aria-labelledby={`h-${hora.bloco.codigo}`}>
                <Ornamento tipo="curto" />
                <h2 id={`h-${hora.bloco.codigo}`} className="fd-h3">{hora.bloco.nome}</h2>
                <p className="fd-texto-longo">{hora.texto}</p>
              </section>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

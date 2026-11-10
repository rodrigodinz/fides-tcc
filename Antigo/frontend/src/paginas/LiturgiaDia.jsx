import { liturgia as api } from "../api/servicos.js";
import { ErroApi } from "../api/cliente.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useDataNaUrl } from "../hooks/useDataNaUrl.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { dataPorExtenso } from "../utils/datas.js";
import { intervaloConhecido, lembrarIntervalo } from "../utils/intervalo.js";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import SeletorData from "../componentes/SeletorData.jsx";
import { AbasLiturgia, AvisoDemonstracao, ErroDeData } from "../componentes/Liturgia.jsx";
import { Carregando } from "../componentes/Estados.jsx";

function Bloco({ rotulo, texto, citacao }) {
  return (
    <section className="fd-bloco">
      <Ornamento tipo="curto" />
      <h2 className="fd-h3">{rotulo}</h2>
      <p className={`fd-texto-longo${citacao ? " fd-citacao" : ""}`}>{texto}</p>
    </section>
  );
}

export default function LiturgiaDia() {
  useTitulo("Liturgia do Dia");
  const { data, invalida, definir } = useDataNaUrl();
  const c = useConsulta(`liturgia:dia:${data ?? "hoje"}:${invalida}`, (signal) => {
    if (invalida) return Promise.reject(new ErroApi({ codigo: "PARAMETRO_INVALIDO", mensagem: "Data inválida." }));
    return api.dia(data, { signal }).then((d) => { lembrarIntervalo(d.intervalo); return d; });
  });
  const l = c.estado === "sucesso" ? c.dados : null;
  const intervalo = l?.intervalo ?? intervaloConhecido();
  const dataAtual = l?.data ?? data ?? intervalo?.hoje;

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Liturgia do Dia" rotulo={dataAtual ? dataPorExtenso(dataAtual) : "Liturgia"} lead={l?.santo_celebrado || null} />
      <AbasLiturgia data={data} />
      {intervalo && dataAtual && <SeletorData data={dataAtual} intervalo={intervalo} aoMudar={(iso) => definir(iso, intervalo)} />}
      <div className="fd-blocos">
        {c.estado === "carregando" && <Carregando tipo="texto" quantidade={6} texto="Carregando a liturgia…" />}
        {c.estado === "erro" && <ErroDeData erro={c.erro} aoVoltarHoje={() => definir(undefined)} aoTentar={c.recarregar} />}
        {l && (
          <>
            <AvisoDemonstracao texto={l.aviso} />
            {l.primeira_leitura && <Bloco rotulo="Primeira Leitura" texto={l.primeira_leitura} />}
            {l.salmo && <Bloco rotulo="Salmo Responsorial" texto={l.salmo} citacao />}
            {l.segunda_leitura && <Bloco rotulo="Segunda Leitura" texto={l.segunda_leitura} />}
            {l.evangelho && <Bloco rotulo="Evangelho" texto={l.evangelho} />}
            {!l.primeira_leitura && !l.salmo && !l.evangelho && !l.segunda_leitura && <p className="fd-aux">As leituras desta data não foram cadastradas.</p>}
          </>
        )}
      </div>
    </div>
  );
}

import { liturgia as api } from "../api/servicos.js";
import { ErroApi } from "../api/cliente.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useDataNaUrl } from "../hooks/useDataNaUrl.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { dataPorExtenso } from "../utils/datas.js";
import { intervaloConhecido, lembrarIntervalo } from "../utils/intervalo.js";
import { ordenarHoras } from "../utils/liturgia.js";
import { CabecalhoPagina } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import SeletorData from "../componentes/SeletorData.jsx";
import { AbasLiturgia, AvisoDemonstracao, ErroDeData } from "../componentes/Liturgia.jsx";
import { Carregando, EstadoVazio } from "../componentes/Estados.jsx";


export default function LiturgiaHoras() {
  useTitulo("Liturgia das Horas");
  const { data, invalida, definir } = useDataNaUrl();
  const c = useConsulta(`liturgia:horas:${data ?? "hoje"}:${invalida}`, (signal) => {
    if (invalida) return Promise.reject(new ErroApi({ codigo: "PARAMETRO_INVALIDO", mensagem: "Data inválida." }));
    return api.horas(data, undefined, { signal }).then((d) => { lembrarIntervalo(d.intervalo); return d; });
  }, { vazio: (d) => d.horas.length === 0 });
  const r = c.dados;
  const intervalo = r?.intervalo ?? intervaloConhecido();
  const dataAtual = r?.data ?? data ?? intervalo?.hoje;

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Liturgia das Horas" rotulo={dataAtual ? dataPorExtenso(dataAtual) : "Liturgia"} lead="Laudes, Horas médias e Vésperas." />
      <AbasLiturgia data={data} />
      {intervalo && dataAtual && <SeletorData data={dataAtual} intervalo={intervalo} aoMudar={(iso) => definir(iso, intervalo)} />}
      <div className="fd-blocos">
        {c.estado === "carregando" && <Carregando tipo="texto" quantidade={6} texto="Carregando a Liturgia das Horas…" />}
        {c.estado === "erro" && <ErroDeData erro={c.erro} aoVoltarHoje={() => definir(undefined)} aoTentar={c.recarregar} />}
        {c.estado === "vazio" && <><AvisoDemonstracao texto={r.aviso} /><EstadoVazio titulo="Sem Liturgia das Horas para esta data" texto="Escolha outra data no período disponível." /></>}
        {c.estado === "sucesso" && (
          <>
            <AvisoDemonstracao texto={r.aviso} />
            {ordenarHoras(r.horas).map((h) => (
              <section key={h.bloco.codigo} className="fd-bloco" aria-labelledby={`h-${h.bloco.codigo}`}>
                <Ornamento tipo="curto" />
                <h2 id={`h-${h.bloco.codigo}`} className="fd-h3">{h.bloco.nome}</h2>
                <p className="fd-texto-longo">{h.texto}</p>
              </section>
            ))}
          </>
        )}
      </div>
    </div>
  );
}

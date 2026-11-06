import { Link } from "react-router-dom";
import { agenda as api } from "../api/servicos.js";
import { ErroApi } from "../api/cliente.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useDataNaUrl } from "../hooks/useDataNaUrl.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { dataPorExtenso } from "../utils/datas.js";
import { intervaloConhecido, lembrarIntervalo } from "../utils/intervalo.js";
import { ordenarHoras } from "../utils/liturgia.js";
import { CabecalhoPagina, TituloSecao } from "../componentes/Estrutura.jsx";
import SeletorData from "../componentes/SeletorData.jsx";
import Card from "../componentes/Card.jsx";
import Icone from "../componentes/Icone.jsx";
import { BotaoLink } from "../componentes/Botao.jsx";
import { AvisoDemonstracao, ErroDeData } from "../componentes/Liturgia.jsx";
import { Carregando } from "../componentes/Estados.jsx";

export default function Agenda() {
  useTitulo("Agenda do dia");
  const { data, invalida, definir } = useDataNaUrl();
  const c = useConsulta(`agenda:${data ?? "hoje"}:${invalida}`, (signal) => {
    if (invalida) return Promise.reject(new ErroApi({ codigo: "PARAMETRO_INVALIDO", mensagem: "Data inválida." }));
    return api.doDia(data, { signal }).then((d) => { lembrarIntervalo(d.intervalo); return d; });
  });
  const a = c.estado === "sucesso" ? c.dados : null;
  const intervalo = a?.intervalo ?? intervaloConhecido();
  const dataAtual = a?.data ?? data ?? intervalo?.hoje;
  const q = a ? `?data=${a.data}` : "";

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Agenda do dia" rotulo={dataAtual ? dataPorExtenso(dataAtual) : "Agenda"} lead="A liturgia e as novenas em andamento na data escolhida." />
      {intervalo && dataAtual && <SeletorData data={dataAtual} intervalo={intervalo} aoMudar={(iso) => definir(iso, intervalo)} />}
      {c.estado === "carregando" && <div className="fd-secao"><Carregando quantidade={3} texto="Carregando a agenda…" /></div>}
      {c.estado === "erro" && <div className="fd-secao fd-leitura" style={{ marginInline: "auto" }}><ErroDeData erro={c.erro} aoVoltarHoje={() => definir(undefined)} aoTentar={c.recarregar} /></div>}
      {a && (
        <>
          <section className="fd-secao" aria-labelledby="ag-novenas">
            <TituloSecao id="ag-novenas" titulo="Novenas em andamento" />
            {a.novenas_em_andamento.length === 0 ? <p className="fd-aux">Nenhuma novena em andamento nesta data. <Link className="fd-link" to="/novenas">Ver todas as novenas</Link></p> : (
              <div className="fd-grade fd-grade--2">
                {a.novenas_em_andamento.map((n) => (
                  <Card key={n.agenda_id} destaque titulo={n.novena.titulo} para={`/novenas/${n.novena.id}`} rotulo={`Dia ${n.dia_atual} de ${n.total_dias}`} meta={n.novena.santo?.nome}
                    acoes={<BotaoLink variante="especial" to={`/novenas/${n.novena.id}/dia/${n.dia_atual}`}>Ler o dia {n.dia_atual}</BotaoLink>} />
                ))}
              </div>
            )}
          </section>
          <section className="fd-secao" aria-labelledby="ag-liturgia">
            <TituloSecao id="ag-liturgia" titulo="Liturgia" />
            <AvisoDemonstracao texto={a.aviso} />
            <div className="fd-grade fd-grade--2" style={{ marginTop: 24 }}>
              <Card titulo="Liturgia do Dia" para={`/liturgia${q}`} meta={a.liturgia_dia?.santo_celebrado ?? null}>
                {a.liturgia_dia ? (
                  <ul className="fd-lista" style={{ marginTop: 12 }}>
                    <li>Primeira Leitura</li><li>Salmo Responsorial</li>{a.liturgia_dia.segunda_leitura && <li>Segunda Leitura</li>}<li>Evangelho</li>
                  </ul>
                ) : <p className="fd-card__corpo-texto">Não há Liturgia do Dia cadastrada para esta data.</p>}
              </Card>
              <Card titulo="Liturgia das Horas" para={`/liturgia/horas${q}`}>
                {a.liturgia_horas.length > 0 ? (
                  <ul className="fd-lista" style={{ marginTop: 12 }}>{ordenarHoras(a.liturgia_horas).map((h) => <li key={h.bloco.codigo}><Icone nome="horas" className="fd-ico--inline" /> {h.bloco.nome}</li>)}</ul>
                ) : <p className="fd-card__corpo-texto">Não há Liturgia das Horas cadastrada para esta data.</p>}
              </Card>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

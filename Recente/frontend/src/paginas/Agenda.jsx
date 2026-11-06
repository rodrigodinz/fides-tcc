import { Link } from "react-router-dom";
import { servicoAgenda } from "../api/servicos.js";
import { ErroDaApi } from "../api/cliente.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useDataNaUrl } from "../hooks/useDataNaUrl.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { periodoConhecido, lembrarPeriodo } from "../utils/periodo.js";
import { ordenarHorasDaLiturgia } from "../utils/liturgia.js";
import { CabecalhoPagina, TituloSecao } from "../componentes/Estrutura.jsx";
import SeletorData from "../componentes/SeletorData.jsx";
import Card from "../componentes/Card.jsx";
import Icone from "../componentes/Icone.jsx";
import { BotaoLink } from "../componentes/Botao.jsx";
import { AvisoDemonstracao, ErroDeData } from "../componentes/Liturgia.jsx";
import { Carregando } from "../componentes/Estados.jsx";

// Agenda do dia: novenas em andamento e liturgia de uma data (GET /agenda).
export default function Agenda() {
  useTitulo("Agenda do dia");
  const { data, dataInvalida, definirData } = useDataNaUrl();
  const consultaDaAgenda = useConsulta(`agenda:${data ?? "hoje"}:${dataInvalida}`, (signal) => {
    // data digitada errada na URL nem chega a chamar a API
    if (dataInvalida) return Promise.reject(new ErroDaApi({ codigo: "PARAMETRO_INVALIDO", mensagem: "Data inválida." }));
    return servicoAgenda.verConteudosDoDia(data, { signal }).then((conteudos) => { lembrarPeriodo(conteudos.periodo); return conteudos; });
  });
  const conteudosDoDia = consultaDaAgenda.estado === "sucesso" ? consultaDaAgenda.dados : null;
  const periodo = conteudosDoDia?.periodo ?? periodoConhecido();
  const dataExibida = conteudosDoDia?.data ?? data ?? periodo?.hoje;
  const parametroDaData = conteudosDoDia ? `?data=${conteudosDoDia.data}` : "";

  return (
    <div className="fd-container fd-pagina">
      <CabecalhoPagina titulo="Agenda do dia" rotulo={dataExibida ? escreverDataPorExtenso(dataExibida) : "Agenda"} textoDeAbertura="A liturgia e as novenas em andamento na data escolhida." />
      {periodo && dataExibida && <SeletorData data={dataExibida} periodo={periodo} aoMudarData={(dataEscolhida) => definirData(dataEscolhida, periodo)} />}
      {consultaDaAgenda.estado === "carregando" && <div className="fd-secao"><Carregando quantidade={3} texto="Carregando a agenda…" /></div>}
      {consultaDaAgenda.estado === "erro" && (
        <div className="fd-secao fd-leitura" style={{ marginInline: "auto" }}>
          <ErroDeData erro={consultaDaAgenda.erro} aoVoltarParaHoje={() => definirData(undefined)} aoTentarNovamente={consultaDaAgenda.recarregar} />
        </div>
      )}
      {conteudosDoDia && (
        <>
          <section className="fd-secao" aria-labelledby="ag-novenas">
            <TituloSecao id="ag-novenas" titulo="Novenas em andamento" />
            {conteudosDoDia.novenas_em_andamento.length === 0 ? (
              <p className="fd-aux">Nenhuma novena em andamento nesta data. <Link className="fd-link" to="/novenas">Ver todas as novenas</Link></p>
            ) : (
              <div className="fd-grade fd-grade--2">
                {conteudosDoDia.novenas_em_andamento.map((novenaEmAndamento) => (
                  <Card key={novenaEmAndamento.agenda_id} destaque titulo={novenaEmAndamento.novena.titulo} para={`/novenas/${novenaEmAndamento.novena.id}`}
                    rotulo={`Dia ${novenaEmAndamento.dia_atual} de ${novenaEmAndamento.total_dias}`} meta={novenaEmAndamento.novena.santo?.nome}
                    acoes={<BotaoLink variante="especial" to={`/novenas/${novenaEmAndamento.novena.id}/dia/${novenaEmAndamento.dia_atual}`}>Ler o dia {novenaEmAndamento.dia_atual}</BotaoLink>} />
                ))}
              </div>
            )}
          </section>
          <section className="fd-secao" aria-labelledby="ag-liturgia">
            <TituloSecao id="ag-liturgia" titulo="Liturgia" />
            <AvisoDemonstracao texto={conteudosDoDia.aviso} />
            <div className="fd-grade fd-grade--2" style={{ marginTop: 24 }}>
              <Card titulo="Liturgia do Dia" para={`/liturgia${parametroDaData}`} meta={conteudosDoDia.liturgia_do_dia?.santo_celebrado ?? null}>
                {conteudosDoDia.liturgia_do_dia ? (
                  <ul className="fd-lista" style={{ marginTop: 12 }}>
                    <li>Primeira Leitura</li><li>Salmo Responsorial</li>{conteudosDoDia.liturgia_do_dia.segunda_leitura && <li>Segunda Leitura</li>}<li>Evangelho</li>
                  </ul>
                ) : <p className="fd-card__corpo-texto">Não há Liturgia do Dia cadastrada para esta data.</p>}
              </Card>
              <Card titulo="Liturgia das Horas" para={`/liturgia/horas${parametroDaData}`}>
                {conteudosDoDia.liturgia_das_horas.length > 0 ? (
                  <ul className="fd-lista" style={{ marginTop: 12 }}>
                    {ordenarHorasDaLiturgia(conteudosDoDia.liturgia_das_horas).map((hora) => (
                      <li key={hora.bloco.codigo}><Icone nome="horas" className="fd-ico--inline" /> {hora.bloco.nome}</li>
                    ))}
                  </ul>
                ) : <p className="fd-card__corpo-texto">Não há Liturgia das Horas cadastrada para esta data.</p>}
              </Card>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

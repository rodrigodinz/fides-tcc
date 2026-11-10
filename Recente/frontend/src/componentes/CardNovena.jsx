import Card from "./Card.jsx";
import { BotaoLink } from "./Botao.jsx";
import { descreverAgendaDaNovena } from "../utils/novena.js";

// card da novena; em andamento ganha destaque e botão para ler o dia atual
export default function CardNovena({ novena, nivel = 2 }) {
  const situacaoDaAgenda = descreverAgendaDaNovena(novena.agenda, novena.total_dias);
  const novenaEmAndamento = situacaoDaAgenda.tipo === "em_andamento";
  const informacoesDoCard = [novena.santo?.nome, situacaoDaAgenda.tipo === "agendada" ? situacaoDaAgenda.texto : null].filter(Boolean).join(" · ");
  return (
    <Card destaque={novenaEmAndamento} nivel={nivel} titulo={novena.titulo} para={`/novenas/${novena.id}`}
      rotulo={novenaEmAndamento ? `${situacaoDaAgenda.rotulo} · ${situacaoDaAgenda.texto}` : situacaoDaAgenda.rotulo}
      meta={informacoesDoCard || null}
      acoes={novenaEmAndamento ? <BotaoLink variante="especial" to={`/novenas/${novena.id}/dia/${situacaoDaAgenda.diaAtual}`}>Ler o dia {situacaoDaAgenda.diaAtual}</BotaoLink> : null}>
      {novena.descricao && <p className="fd-card__corpo-texto">{novena.descricao}</p>}
    </Card>
  );
}

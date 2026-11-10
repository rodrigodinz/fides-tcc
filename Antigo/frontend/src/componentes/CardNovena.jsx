import Card from "./Card.jsx";
import { BotaoLink } from "./Botao.jsx";
import { descreverAgenda } from "../utils/novena.js";

/** Card de novena com a situação da agenda global; em andamento vira card destacado. */
export default function CardNovena({ novena, nivel = 2 }) {
  const s = descreverAgenda(novena.agenda, novena.total_dias);
  const andamento = s.tipo === "em_andamento";
  return (
    <Card destaque={andamento} nivel={nivel} titulo={novena.titulo} para={`/novenas/${novena.id}`}
      rotulo={andamento ? `${s.rotulo} · ${s.texto}` : s.rotulo}
      meta={[novena.santo?.nome, s.tipo === "agendada" ? s.texto : null].filter(Boolean).join(" · ") || null}
      acoes={andamento ? <BotaoLink variante="especial" to={`/novenas/${novena.id}/dia/${s.diaAtual}`}>Ler o dia {s.diaAtual}</BotaoLink> : null}>
      {novena.descricao && <p className="fd-card__corpo-texto">{novena.descricao}</p>}
    </Card>
  );
}

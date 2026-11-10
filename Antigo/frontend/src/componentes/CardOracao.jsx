import { useId, useState } from "react";
import Card from "./Card.jsx";
import { Botao } from "./Botao.jsx";

/** Oração: card horizontal só de texto (sem imagem), com leitura integral no próprio card. */
export default function CardOracao({ oracao, nivel = 3, abertaInicial = false }) {
  const [aberta, setAberta] = useState(abertaInicial);
  const id = useId();
  const longa = oracao.texto.length > 220;
  const meta = [oracao.basica ? "Oração básica" : null, oracao.santo?.nome].filter(Boolean).join(" · ");
  return (
    <Card simples titulo={oracao.titulo} nivel={nivel} meta={meta || null} className="fd-oracao">
      <p id={`oracao-${id}`} className={`fd-oracao__texto fd-texto-longo${longa && !aberta ? " is-recolhido" : ""}`}>{oracao.texto}</p>
      {(longa || oracao.momentos?.length > 0) && (
        <div className="fd-oracao__rodape">
          {oracao.momentos?.length > 0 ? (
            <ul className="fd-etiquetas" aria-label="Momentos do dia">{oracao.momentos.map((m) => <li key={m.id} className="fd-etiqueta">{m.nome}</li>)}</ul>
          ) : <span />}
          {longa && (
            <Botao variante="texto" pequeno aria-expanded={aberta} aria-controls={`oracao-${id}`} onClick={() => setAberta((a) => !a)}>
              {aberta ? "Recolher" : "Ler a oração inteira"}
            </Botao>
          )}
        </div>
      )}
    </Card>
  );
}

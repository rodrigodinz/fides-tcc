import { useId, useState } from "react";
import Card from "./Card.jsx";
import { Botao } from "./Botao.jsx";

const Tamanho_De_Texto_Longo = 220;

// card da oração; textos longos começam recolhidos com o botão "Ler a oração inteira"
export default function CardOracao({ oracao, nivel = 3, abertaInicialmente = false }) {
  const [oracaoAberta, setOracaoAberta] = useState(abertaInicialmente);
  const idGerado = useId();
  const textoLongo = oracao.texto.length > Tamanho_De_Texto_Longo;
  const informacoesDaOracao = [oracao.basica ? "Oração básica" : null, oracao.santo?.nome].filter(Boolean).join(" · ");
  return (
    <Card simples titulo={oracao.titulo} nivel={nivel} meta={informacoesDaOracao || null} className="fd-oracao">
      <p id={`oracao-${idGerado}`} className={`fd-oracao__texto fd-texto-longo${textoLongo && !oracaoAberta ? " is-recolhido" : ""}`}>{oracao.texto}</p>
      {(textoLongo || oracao.momentos?.length > 0) && (
        <div className="fd-oracao__rodape">
          {oracao.momentos?.length > 0 ? (
            <ul className="fd-etiquetas" aria-label="Momentos do dia">{oracao.momentos.map((momento) => <li key={momento.id} className="fd-etiqueta">{momento.nome}</li>)}</ul>
          ) : <span />}
          {textoLongo && (
            <Botao variante="texto" pequeno aria-expanded={oracaoAberta} aria-controls={`oracao-${idGerado}`} onClick={() => setOracaoAberta((estavaAberta) => !estavaAberta)}>
              {oracaoAberta ? "Recolher" : "Ler a oração inteira"}
            </Botao>
          )}
        </div>
      )}
    </Card>
  );
}

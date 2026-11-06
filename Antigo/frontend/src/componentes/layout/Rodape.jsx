import { Link } from "react-router-dom";
import simbolo from "../../assets/simbolo-fides.svg";
import { MODULOS } from "../../navegacao.js";

/** Rodapé: faixa azul com links claros (contraste 13,6:1) e faixa clara de créditos. */
export default function Rodape() {
  return (
    <footer className="fd-rodape">
      <div className="fd-rodape__nav fd-escuro">
        <div className="fd-container fd-rodape__nav-inner">
          <Link to="/" className="fd-rodape__marca"><img src={simbolo} alt="" width="30" height="40" />FIDES</Link>
          <nav aria-label="Rodapé">
            <ul>{MODULOS.map((m) => <li key={m.rota}><Link to={m.rota}>{m.nome}</Link></li>)}</ul>
          </nav>
        </div>
      </div>
      <div className="fd-container fd-rodape__creditos">
        <span>Fides · Plataforma Integrada de Conteúdo e Práticas Católicas · Trabalho de Conclusão de Curso</span>
        <span>Liturgia em conteúdo de demonstração: não é o texto oficial.</span>
      </div>
    </footer>
  );
}

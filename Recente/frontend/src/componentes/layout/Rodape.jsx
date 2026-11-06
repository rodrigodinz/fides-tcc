import { Link } from "react-router-dom";
import simboloDoFides from "../../assets/simbolo-fides.svg";
import { Modulos } from "../../navegacao.js";

// rodapé com os links dos módulos e o aviso da liturgia de demonstração
export default function Rodape() {
  return (
    <footer className="fd-rodape">
      <div className="fd-rodape__nav fd-escuro">
        <div className="fd-container fd-rodape__nav-inner">
          <Link to="/" className="fd-rodape__marca"><img src={simboloDoFides} alt="" width="30" height="40" />FIDES</Link>
          <nav aria-label="Rodapé">
            <ul>{Modulos.map((modulo) => <li key={modulo.rota}><Link to={modulo.rota}>{modulo.nome}</Link></li>)}</ul>
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

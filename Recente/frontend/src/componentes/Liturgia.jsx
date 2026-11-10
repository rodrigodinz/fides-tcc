import { Link, useLocation } from "react-router-dom";
import Icone from "./Icone.jsx";
import { Alerta } from "./Estados.jsx";
import { Botao } from "./Botao.jsx";
import { montarMensagemDeErro } from "../api/erros.js";

const Abas_Da_Liturgia = [
  { para: "/liturgia", nome: "Liturgia do Dia", icone: "liturgia" },
  { para: "/liturgia/horas", nome: "Liturgia das Horas", icone: "horas" },
];

const Codigos_De_Erro_De_Data = ["DATA_FORA_DO_INTERVALO", "LITURGIA_NAO_CADASTRADA", "PARAMETRO_INVALIDO"];

// abas Liturgia do Dia / Liturgia das Horas, mantendo a data escolhida
export function AbasLiturgia({ data }) {
  const { pathname: caminhoAtual } = useLocation();
  const parametroDaData = data ? `?data=${data}` : "";
  return (
    <nav aria-label="Liturgia">
      <ul className="fd-abas">
        {Abas_Da_Liturgia.map((aba) => (
          <li key={aba.para}>
            <Link className="fd-aba" to={`${aba.para}${parametroDaData}`} aria-current={caminhoAtual === aba.para ? "page" : undefined}>
              <Icone nome={aba.icone} />{aba.nome}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}

export function AvisoDemonstracao({ texto }) {
  return <Alerta tipo="aviso" titulo="Conteúdo de demonstração" papel="note"><p>{texto}</p></Alerta>;
}

// erros de data (fora do período, sem liturgia) oferecem "Ir para hoje"
export function ErroDeData({ erro, aoVoltarParaHoje, aoTentarNovamente }) {
  const { titulo, texto } = montarMensagemDeErro(erro);
  if (Codigos_De_Erro_De_Data.includes(erro?.codigo)) {
    const dataInvalida = erro.codigo === "PARAMETRO_INVALIDO";
    return (
      <Alerta tipo="info" titulo={dataInvalida ? "Data inválida." : titulo}
        acoes={<Botao variante="secundario" icone="calendario" onClick={aoVoltarParaHoje}>Ir para hoje</Botao>}>
        <p>{dataInvalida ? "Use uma data no formato do calendário." : texto}</p>
      </Alerta>
    );
  }
  return (
    <Alerta tipo="erro" titulo={titulo}
      acoes={aoTentarNovamente && <Botao variante="secundario" icone="recarregar" onClick={aoTentarNovamente}>Tentar novamente</Botao>}>
      <p>{texto}</p>
    </Alerta>
  );
}

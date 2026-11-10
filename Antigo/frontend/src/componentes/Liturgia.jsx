import { Link, useLocation } from "react-router-dom";
import Icone from "./Icone.jsx";
import { Alerta } from "./Estados.jsx";
import { Botao } from "./Botao.jsx";
import { mensagemErro } from "../api/erros.js";

/** Alterna entre Liturgia do Dia e das Horas mantendo a data escolhida. */
export function AbasLiturgia({ data }) {
  const { pathname } = useLocation();
  const q = data ? `?data=${data}` : "";
  const abas = [{ para: "/liturgia", nome: "Liturgia do Dia", icone: "liturgia" }, { para: "/liturgia/horas", nome: "Liturgia das Horas", icone: "horas" }];
  return (
    <nav aria-label="Liturgia">
      <ul className="fd-abas">
        {abas.map((a) => (
          <li key={a.para}><Link className="fd-aba" to={`${a.para}${q}`} aria-current={pathname === a.para ? "page" : undefined}><Icone nome={a.icone} />{a.nome}</Link></li>
        ))}
      </ul>
    </nav>
  );
}

/** Aviso enviado pela API: conteúdo demonstrativo, não liturgia oficial. */
export function AvisoDemonstracao({ texto }) {
  return <Alerta tipo="aviso" titulo="Conteúdo de demonstração" papel="note"><p>{texto}</p></Alerta>;
}

/** Erros esperados de data: fora da janela (±7 dias) ou sem registro demonstrativo. */
export function ErroDeData({ erro, aoVoltarHoje, aoTentar }) {
  const { titulo, texto } = mensagemErro(erro);
  if (erro?.codigo === "DATA_FORA_DO_INTERVALO" || erro?.codigo === "LITURGIA_NAO_CADASTRADA" || erro?.codigo === "PARAMETRO_INVALIDO") {
    return (
      <Alerta tipo="info" titulo={erro.codigo === "PARAMETRO_INVALIDO" ? "Data inválida." : titulo}
        acoes={<Botao variante="secundario" icone="calendario" onClick={aoVoltarHoje}>Ir para hoje</Botao>}>
        <p>{erro.codigo === "PARAMETRO_INVALIDO" ? "Use uma data no formato do calendário." : texto}</p>
      </Alerta>
    );
  }
  return <Alerta tipo="erro" titulo={titulo} acoes={aoTentar && <Botao variante="secundario" icone="recarregar" onClick={aoTentar}>Tentar novamente</Botao>}><p>{texto}</p></Alerta>;
}

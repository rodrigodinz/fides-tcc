import { mensagemErro, ehRecuperavel } from "../api/erros.js";
import Icone from "./Icone.jsx";
import Ornamento from "./Ornamento.jsx";
import { Botao, BotaoLink } from "./Botao.jsx";

export function Alerta({ tipo = "info", titulo, children, acoes, papel }) {
  const icone = tipo === "erro" ? "alerta" : tipo === "sucesso" ? "check" : "info";
  const role = papel ?? (tipo === "erro" ? "alert" : "status");
  return (
    <div className={`fd-alerta fd-alerta--${tipo}`} role={role}>
      <Icone nome={icone} />
      <div>
        {titulo && <strong className="fd-alerta__titulo">{titulo}</strong>}
        {children}
        {acoes && <div className="fd-alerta__acoes">{acoes}</div>}
      </div>
    </div>
  );
}

/** Erro amigável com "Tentar novamente" quando a falha é recuperável. */
export function EstadoErro({ erro, oQue, aoTentar, acaoExtra }) {
  const { titulo, texto } = mensagemErro(erro, oQue);
  return (
    <Alerta tipo="erro" titulo={titulo} acoes={(aoTentar && ehRecuperavel(erro)) || acaoExtra ? <>
      {aoTentar && ehRecuperavel(erro) && <Botao variante="secundario" icone="recarregar" onClick={aoTentar}>Tentar novamente</Botao>}
      {acaoExtra}
    </> : null}>
      <p>{texto}</p>
    </Alerta>
  );
}

export function EstadoVazio({ titulo, texto, acao }) {
  return (
    <div className="fd-vazio" role="status">
      <Ornamento tipo="curto" />
      <h3 className="fd-h4">{titulo}</h3>
      {texto && <p className="fd-aux">{texto}</p>}
      {acao && <div className="fd-vazio__acoes">{acao}</div>}
    </div>
  );
}

export function NaoEncontrado({ titulo = "Conteúdo não encontrado", voltar }) {
  return (
    <div className="fd-vazio">
      <Ornamento tipo="curto" />
      <h2 className="fd-h3">{titulo}</h2>
      <p className="fd-aux">O endereço pode estar incorreto ou o conteúdo não existe mais.</p>
      {voltar && <div className="fd-vazio__acoes"><BotaoLink variante="secundario" icone="esquerda" to={voltar.para}>{voltar.texto}</BotaoLink></div>}
    </div>
  );
}

/** Esqueletos discretos; o texto escondido informa o carregamento aos leitores de tela. */
export function Carregando({ tipo = "cards", quantidade = 3, texto = "Carregando…" }) {
  const itens = Array.from({ length: quantidade });
  return (
    <div aria-busy="true" role="status">
      <span className="fd-sr">{texto}</span>
      {tipo === "texto" ? (
        <div className="fd-leitura" style={{ display: "grid", gap: 10 }}>
          <span className="fd-esqueleto" style={{ height: 26, width: "55%" }} />
          {itens.map((_, i) => <span key={i} className="fd-esqueleto" style={{ height: 14, width: `${92 - i * 9}%` }} />)}
        </div>
      ) : tipo === "santos" ? (
        <div className="fd-grade fd-grade--3">{itens.map((_, i) => <span key={i} className="fd-esqueleto fd-esqueleto--retrato" />)}</div>
      ) : (
        <div className="fd-grade fd-grade--2">{itens.map((_, i) => <span key={i} className="fd-esqueleto fd-esqueleto--card" />)}</div>
      )}
    </div>
  );
}

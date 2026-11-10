import { montarMensagemDeErro, ehErroRecuperavel } from "../api/erros.js";
import Icone from "./Icone.jsx";
import Ornamento from "./Ornamento.jsx";
import { Botao, BotaoLink } from "./Botao.jsx";

export function Alerta({ tipo = "info", titulo, children, acoes, papel }) {
  const nomeDoIcone = tipo === "erro" ? "alerta" : tipo === "sucesso" ? "check" : "info";
  const papelAcessivel = papel ?? (tipo === "erro" ? "alert" : "status");
  return (
    <div className={`fd-alerta fd-alerta--${tipo}`} role={papelAcessivel}>
      <Icone nome={nomeDoIcone} />
      <div>
        {titulo && <strong className="fd-alerta__titulo">{titulo}</strong>}
        {children}
        {acoes && <div className="fd-alerta__acoes">{acoes}</div>}
      </div>
    </div>
  );
}

// mensagem de erro amigável; o botão "Tentar novamente" só aparece em erros que podem passar (rede, servidor)
export function EstadoErro({ erro, conteudoBuscado, aoTentarNovamente, acaoExtra }) {
  const { titulo, texto } = montarMensagemDeErro(erro, conteudoBuscado);
  const podeTentarNovamente = aoTentarNovamente && ehErroRecuperavel(erro);
  return (
    <Alerta tipo="erro" titulo={titulo} acoes={podeTentarNovamente || acaoExtra ? <>
      {podeTentarNovamente && <Botao variante="secundario" icone="recarregar" onClick={aoTentarNovamente}>Tentar novamente</Botao>}
      {acaoExtra}
    </> : null}>
      <p>{texto}</p>
    </Alerta>
  );
}

// quando a busca deu certo mas não há resultados (não é erro)
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

// esqueletos cinza enquanto os dados chegam
export function Carregando({ tipo = "cards", quantidade = 3, texto = "Carregando…" }) {
  const esqueletos = Array.from({ length: quantidade });
  return (
    <div aria-busy="true" role="status">
      <span className="fd-sr">{texto}</span>
      {tipo === "texto" ? (
        <div className="fd-leitura" style={{ display: "grid", gap: 10 }}>
          <span className="fd-esqueleto" style={{ height: 26, width: "55%" }} />
          {esqueletos.map((_, posicao) => <span key={posicao} className="fd-esqueleto" style={{ height: 14, width: `${92 - posicao * 9}%` }} />)}
        </div>
      ) : tipo === "santos" ? (
        <div className="fd-grade fd-grade--3">{esqueletos.map((_, posicao) => <span key={posicao} className="fd-esqueleto fd-esqueleto--retrato" />)}</div>
      ) : (
        <div className="fd-grade fd-grade--2">{esqueletos.map((_, posicao) => <span key={posicao} className="fd-esqueleto fd-esqueleto--card" />)}</div>
      )}
    </div>
  );
}

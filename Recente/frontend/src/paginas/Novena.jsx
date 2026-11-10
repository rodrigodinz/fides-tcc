import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { servicoNovenas } from "../api/servicos.js";
import { ehErroDeNaoEncontrado } from "../api/erros.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { useNovenaPessoal } from "../hooks/useNovenaPessoal.js";
import { lerIdDaUrl } from "../utils/paginacao.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { descreverAgendaDaNovena, escolherDiaInicial } from "../utils/novena.js";
import { Limite_De_Caracteres_Dos_Pedidos } from "../estado/novenaPessoal.js";
import { CabecalhoPagina, Migalhas } from "../componentes/Estrutura.jsx";
import CalendarioNovena from "../componentes/CalendarioNovena.jsx";
import Icone from "../componentes/Icone.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import { Botao, BotaoLink } from "../componentes/Botao.jsx";
import { Alerta, Carregando, EstadoErro, NaoEncontrado } from "../componentes/Estados.jsx";
import { Confirmacao } from "../componentes/Retorno.jsx";
import { useToast } from "../componentes/toast.js";

// quadro da agenda: situação, período e "Dia X de 9"
function AgendaDaNovena({ novena }) {
  const situacaoDaAgenda = descreverAgendaDaNovena(novena.agenda, novena.total_dias);
  const agenda = novena.agenda;
  return (
    <section className="fd-card fd-card--simples" aria-labelledby="agenda-titulo">
      <div className="fd-agenda-resumo">
        <div>
          <h2 id="agenda-titulo" className="fd-rotulo">Agenda da novena</h2>
          <p className={`fd-situacao fd-situacao--${situacaoDaAgenda.tipo}`} style={{ marginTop: 6 }}>{situacaoDaAgenda.rotulo}</p>
          {agenda && (
            <p className="fd-aux" style={{ marginTop: 4 }}>
              De {escreverDataPorExtenso(agenda.data_inicio, { comDiaDaSemana: false })} a {escreverDataPorExtenso(agenda.data_fim, { comDiaDaSemana: false })}
            </p>
          )}
        </div>
        {situacaoDaAgenda.tipo === "em_andamento"
          ? <p className="fd-dia-x" aria-label={situacaoDaAgenda.texto}><small>Dia</small>{agenda.dia_atual}<small>de {novena.total_dias}</small></p>
          : <p className="fd-h4" style={{ color: "var(--azul-profundo)" }}>{situacaoDaAgenda.tipo === "agendada" ? situacaoDaAgenda.texto : "Sem agenda ativa"}</p>}
      </div>
      <p className="fd-aux" style={{ marginTop: 12 }}>
        {situacaoDaAgenda.tipo === "sem_agenda"
          ? "Os nove dias podem ser lidos livremente; não há datas definidas."
          : "O dia atual segue a agenda da novena e é o mesmo para todos. Você pode ler qualquer dia."}
      </p>
    </section>
  );
}

// Parte pessoal: marcar dia rezado e escrever pedidos. Tudo fica só no navegador;
// apagar pede confirmação porque não dá para recuperar.
function NesteDispositivo({ novenaId, numeroDoDia, totalDias, novenaPessoal }) {
  const avisar = useToast();
  const [textoDosPedidos, setTextoDosPedidos] = useState(novenaPessoal.pedidos);
  const [confirmacaoPendente, setConfirmacaoPendente] = useState(null);
  useEffect(() => { setTextoDosPedidos(novenaPessoal.pedidos); }, [novenaPessoal.pedidos, novenaId]);
  const diaMarcado = novenaPessoal.marcados.includes(numeroDoDia);
  const pedidosAlterados = textoDosPedidos !== novenaPessoal.pedidos;
  const vaiApagarPedidos = confirmacaoPendente === "pedidos";

  const alternarDiaRezado = () => {
    if (novenaPessoal.alternarDiaRezado(numeroDoDia)) {
      avisar(diaMarcado ? `Marcação do dia ${numeroDoDia} removida.` : `Dia ${numeroDoDia} marcado como rezado neste dispositivo.`);
    }
  };
  const guardarPedidos = () => { if (novenaPessoal.salvarPedidos(textoDosPedidos)) avisar("Pedidos guardados neste dispositivo."); };
  const confirmarLimpeza = () => {
    const limpou = vaiApagarPedidos ? novenaPessoal.limparPedidos() : novenaPessoal.limparMarcacoes();
    if (limpou) avisar(vaiApagarPedidos ? "Pedidos apagados deste dispositivo." : "Marcações removidas deste dispositivo.");
    setConfirmacaoPendente(null);
  };

  if (!novenaPessoal.armazenamentoEstaDisponivel) {
    return (
      <Alerta tipo="aviso" titulo="Marcações e pedidos indisponíveis" papel="note">
        <p>Este navegador não permite guardar dados no dispositivo (por exemplo, em navegação privada). O conteúdo da novena continua disponível.</p>
      </Alerta>
    );
  }
  return (
    <section className="fd-pessoal" aria-labelledby="pessoal-titulo">
      <h2 id="pessoal-titulo" className="fd-h4" style={{ display: "flex", gap: 10, alignItems: "center" }}><Icone nome="dispositivo" />Neste dispositivo</h2>
      <p className="fd-aux" style={{ marginTop: 6 }}>Suas marcações e pedidos ficam só neste aparelho. Não são enviados e não mudam o dia da agenda.</p>
      <label className="fd-marcar" style={{ marginTop: 16 }}>
        <input type="checkbox" checked={diaMarcado} onChange={alternarDiaRezado} />
        Rezei o dia {numeroDoDia}
      </label>
      <p className="fd-aux">Você marcou {novenaPessoal.marcados.length} de {totalDias} dias.</p>
      {novenaPessoal.marcados.length > 0 && <Botao variante="texto" pequeno onClick={() => setConfirmacaoPendente("marcacoes")}>Limpar marcações</Botao>}

      <div className="fd-campo" style={{ marginTop: 20 }}>
        <label htmlFor="pedidos">Meus pedidos</label>
        <textarea id="pedidos" className="fd-textarea" value={textoDosPedidos} maxLength={Limite_De_Caracteres_Dos_Pedidos}
          onChange={(evento) => setTextoDosPedidos(evento.target.value)}
          onBlur={() => { if (pedidosAlterados) guardarPedidos(); }} placeholder="Escreva suas intenções para esta novena." />
        <span className="fd-aux">{textoDosPedidos.length}/{Limite_De_Caracteres_Dos_Pedidos} caracteres</span>
      </div>
      <div className="fd-linha-acoes" style={{ marginTop: 12 }}>
        <Botao variante="secundario" icone="check" onClick={guardarPedidos} disabled={!pedidosAlterados}>Guardar pedidos</Botao>
        {novenaPessoal.pedidos && <Botao variante="texto" icone="limpar" onClick={() => setConfirmacaoPendente("pedidos")}>Apagar pedidos</Botao>}
      </div>
      {novenaPessoal.falhouAoGravar && (
        <div style={{ marginTop: 12 }}><Alerta tipo="erro" titulo="Não foi possível guardar">O armazenamento do navegador está cheio ou bloqueado.</Alerta></div>
      )}

      <Confirmacao aberto={confirmacaoPendente !== null}
        titulo={vaiApagarPedidos ? "Apagar seus pedidos desta novena?" : "Limpar suas marcações desta novena?"}
        textoConfirmar={vaiApagarPedidos ? "Apagar pedidos" : "Limpar marcações"} textoCancelar="Manter"
        aoCancelar={() => setConfirmacaoPendente(null)}
        aoConfirmar={confirmarLimpeza}>
        <p>Eles estão guardados só neste dispositivo e não poderão ser recuperados.</p>
      </Confirmacao>
    </section>
  );
}

// reflexão e orações do dia escolhido (GET /novenas/{id}/dias/{n})
function ConteudoDoDia({ novenaId, numeroDoDia }) {
  const consultaDoDia = useConsulta(`novena:${novenaId}:dia:${numeroDoDia}`, (signal) => servicoNovenas.verDiaDaNovena(novenaId, numeroDoDia, { signal }));
  if (consultaDoDia.estado === "carregando") return <Carregando tipo="texto" quantidade={5} texto={`Carregando o dia ${numeroDoDia}…`} />;
  if (consultaDoDia.estado === "erro") {
    if (ehErroDeNaoEncontrado(consultaDoDia.erro)) {
      return <NaoEncontrado titulo={`Dia ${numeroDoDia} não encontrado`} voltar={{ para: `/novenas/${novenaId}`, texto: "Voltar à novena" }} />;
    }
    return <EstadoErro erro={consultaDoDia.erro} conteudoBuscado={`o dia ${numeroDoDia}`} aoTentarNovamente={consultaDoDia.recarregar} />;
  }
  const diaDaNovena = consultaDoDia.dados;
  return (
    <article aria-labelledby="dia-titulo">
      <p className="fd-rotulo">
        Dia {diaDaNovena.numero_do_dia} de {diaDaNovena.total_dias}{diaDaNovena.data ? ` · ${escreverDataPorExtenso(diaDaNovena.data, { comAno: false })}` : ""}
      </p>
      <h2 id="dia-titulo" className="fd-h2" style={{ marginTop: 4 }}>Reflexão do dia {diaDaNovena.numero_do_dia}</h2>
      <p className="fd-leitura fd-reflexao fd-texto-longo" style={{ marginTop: 16 }}>{diaDaNovena.texto_reflexao}</p>
      <h3 className="fd-h3" style={{ marginTop: 40, marginBottom: 12 }}>Orações do dia</h3>
      {diaDaNovena.oracoes.length === 0 ? <p className="fd-aux">Nenhuma oração base cadastrada para este dia.</p> : diaDaNovena.oracoes.map((oracao, posicao) => (
        <details key={oracao.id} className="fd-expansivel" open={posicao === 0}>
          <summary>{oracao.titulo}<Icone nome="baixo" /></summary>
          <div className="fd-expansivel__corpo"><p className="fd-texto-longo">{oracao.texto}</p></div>
        </details>
      ))}
      <nav className="fd-nav-dias" aria-label="Navegar entre os dias">
        {diaDaNovena.dia_anterior
          ? <BotaoLink variante="secundario" icone="esquerda" to={`/novenas/${novenaId}/dia/${diaDaNovena.dia_anterior}`}>Dia {diaDaNovena.dia_anterior}</BotaoLink>
          : <span />}
        {diaDaNovena.proximo_dia
          ? <BotaoLink variante="secundario" iconeDepois="direita" to={`/novenas/${novenaId}/dia/${diaDaNovena.proximo_dia}`}>Dia {diaDaNovena.proximo_dia}</BotaoLink>
          : <span />}
      </nav>
    </article>
  );
}

// Página da novena. Atende /novenas/:id e /novenas/:id/dia/:numero; sem número, abre no dia atual da agenda.
// Faz duas buscas em paralelo: o detalhe da novena e o calendário dos dias.
export default function Novena() {
  const { id: idEscritoNaUrl, numero: numeroEscritoNaUrl } = useParams();
  const novenaId = lerIdDaUrl(idEscritoNaUrl);
  const numeroDoDiaNaUrl = numeroEscritoNaUrl === undefined ? null : lerIdDaUrl(numeroEscritoNaUrl);
  const consultaDaNovena = useConsulta(`novena:${novenaId}`, (signal) => servicoNovenas.detalharNovena(novenaId, { signal }), { consultaAtiva: novenaId !== null });
  const consultaDosDias = useConsulta(`novena:${novenaId}:dias`, (signal) => servicoNovenas.listarDiasDaNovena(novenaId, { signal }), { consultaAtiva: novenaId !== null });
  const novena = consultaDaNovena.estado === "sucesso" ? consultaDaNovena.dados : null;
  const totalDias = novena?.total_dias ?? 9;
  const novenaPessoal = useNovenaPessoal(novenaId ?? 0, totalDias);
  useTitulo(novena?.titulo ?? "Novena");

  const voltarParaNovenas = { para: "/novenas", texto: "Voltar às novenas" };
  if (novenaId === null || (consultaDaNovena.estado === "erro" && ehErroDeNaoEncontrado(consultaDaNovena.erro))) {
    return <div className="fd-container fd-pagina"><NaoEncontrado titulo="Novena não encontrada" voltar={voltarParaNovenas} /></div>;
  }
  const numeroDoDia = numeroDoDiaNaUrl ?? (novena ? escolherDiaInicial(novena.agenda, totalDias) : null);
  const numeroDoDiaValido = numeroDoDia !== null && numeroDoDia >= 1 && numeroDoDia <= totalDias;

  return (
    <div className="fd-container fd-pagina">
      <Migalhas itens={[{ texto: "Início", para: "/" }, { texto: "Novenas", para: "/novenas" }, { texto: novena?.titulo ?? "Novena" }]} />
      {consultaDaNovena.estado === "carregando" && <Carregando tipo="texto" quantidade={4} texto="Carregando a novena…" />}
      {consultaDaNovena.estado === "erro" && <EstadoErro erro={consultaDaNovena.erro} conteudoBuscado="esta novena" aoTentarNovamente={consultaDaNovena.recarregar} />}
      {novena && (
        <>
          <CabecalhoPagina titulo={novena.titulo} rotulo="Novena" textoDeAbertura={novena.descricao}>
            {novena.santo && <p style={{ marginTop: 12 }}><Link className="fd-link fd-link--vinho" to={`/santos/${novena.santo.id}`}>{novena.santo.nome}</Link></p>}
          </CabecalhoPagina>
          <Ornamento tipo="divisor" />
          <div className="fd-novena-topo">
            <AgendaDaNovena novena={novena} />
            {consultaDosDias.estado === "carregando" && <Carregando quantidade={1} texto="Carregando o calendário…" />}
            {consultaDosDias.estado === "erro" && <EstadoErro erro={consultaDosDias.erro} conteudoBuscado="o calendário da novena" aoTentarNovamente={consultaDosDias.recarregar} />}
            {consultaDosDias.estado === "sucesso" && (
              <section aria-labelledby="cal-titulo">
                <h2 id="cal-titulo" className="fd-h3">Os nove dias</h2>
                <CalendarioNovena novenaId={novenaId} dias={consultaDosDias.dados.dias}
                  diaAtual={descreverAgendaDaNovena(consultaDosDias.dados.agenda, totalDias).diaAtual}
                  marcados={novenaPessoal.marcados} diaSelecionado={numeroDoDiaValido ? numeroDoDia : null} />
              </section>
            )}
          </div>
          <div className="fd-novena-dia">
            <div>
              {numeroDoDiaValido
                ? <ConteudoDoDia novenaId={novenaId} numeroDoDia={numeroDoDia} />
                : <NaoEncontrado titulo={`Dia ${numeroEscritoNaUrl} não encontrado`} voltar={{ para: `/novenas/${novenaId}`, texto: "Voltar à novena" }} />}
            </div>
            {numeroDoDiaValido && (
              <div><NesteDispositivo novenaId={novenaId} numeroDoDia={numeroDoDia} totalDias={totalDias} novenaPessoal={novenaPessoal} /></div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

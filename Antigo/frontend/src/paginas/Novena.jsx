import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { novenas as api } from "../api/servicos.js";
import { ehNaoEncontrado } from "../api/erros.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { useNovenaPessoal } from "../hooks/useNovenaPessoal.js";
import { lerId } from "../utils/paginacao.js";
import { dataPorExtenso } from "../utils/datas.js";
import { descreverAgenda, diaInicial } from "../utils/novena.js";
import { LIMITE_PEDIDOS } from "../estado/novenaPessoal.js";
import { CabecalhoPagina, Migalhas } from "../componentes/Estrutura.jsx";
import CalendarioNovena from "../componentes/CalendarioNovena.jsx";
import Icone from "../componentes/Icone.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import { Botao, BotaoLink } from "../componentes/Botao.jsx";
import { Alerta, Carregando, EstadoErro, NaoEncontrado } from "../componentes/Estados.jsx";
import { Confirmacao } from "../componentes/Retorno.jsx";
import { useToast } from "../componentes/toast.js";

/** Agenda global: "Dia X de 9" vem da API e é igual para todos os fiéis. */
function AgendaDaNovena({ novena }) {
  const s = descreverAgenda(novena.agenda, novena.total_dias);
  const a = novena.agenda;
  return (
    <section className="fd-card fd-card--simples" aria-labelledby="agenda-titulo">
      <div className="fd-agenda-resumo">
        <div>
          <h2 id="agenda-titulo" className="fd-rotulo">Agenda da novena</h2>
          <p className={`fd-situacao fd-situacao--${s.tipo}`} style={{ marginTop: 6 }}>{s.rotulo}</p>
          {a && <p className="fd-aux" style={{ marginTop: 4 }}>De {dataPorExtenso(a.data_inicio, { semana: false })} a {dataPorExtenso(a.data_fim, { semana: false })}</p>}
        </div>
        {s.tipo === "em_andamento"
          ? <p className="fd-dia-x" aria-label={s.texto}><small>Dia</small>{a.dia_atual}<small>de {novena.total_dias}</small></p>
          : <p className="fd-h4" style={{ color: "var(--azul-profundo)" }}>{s.tipo === "agendada" ? s.texto : "Sem agenda ativa"}</p>}
      </div>
      <p className="fd-aux" style={{ marginTop: 12 }}>
        {s.tipo === "sem_agenda" ? "Os nove dias podem ser lidos livremente; não há datas definidas." : "O dia atual segue a agenda da novena e é o mesmo para todos. Você pode ler qualquer dia."}
      </p>
    </section>
  );
}

/** Só neste dispositivo: marcar dia como rezado e guardar pedidos. Não altera a agenda. */
function NesteDispositivo({ novenaId, numero, totalDias, pessoal }) {
  const avisar = useToast();
  const [texto, setTexto] = useState(pessoal.pedidos);
  const [confirmar, setConfirmar] = useState(null);
  useEffect(() => { setTexto(pessoal.pedidos); }, [pessoal.pedidos, novenaId]);
  const marcado = pessoal.marcados.includes(numero);
  const alterado = texto !== pessoal.pedidos;

  const alternar = () => { if (pessoal.alternar(numero)) avisar(marcado ? `Marcação do dia ${numero} removida.` : `Dia ${numero} marcado como rezado neste dispositivo.`); };
  const guardar = () => { if (pessoal.salvarPedidos(texto)) avisar("Pedidos guardados neste dispositivo."); };

  if (!pessoal.disponivel) {
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
        <input type="checkbox" checked={marcado} onChange={alternar} />
        Rezei o dia {numero}
      </label>
      <p className="fd-aux">Você marcou {pessoal.marcados.length} de {totalDias} dias.</p>
      {pessoal.marcados.length > 0 && <Botao variante="texto" pequeno onClick={() => setConfirmar("marcacoes")}>Limpar marcações</Botao>}

      <div className="fd-campo" style={{ marginTop: 20 }}>
        <label htmlFor="pedidos">Meus pedidos</label>
        <textarea id="pedidos" className="fd-textarea" value={texto} maxLength={LIMITE_PEDIDOS} onChange={(e) => setTexto(e.target.value)}
          onBlur={() => { if (alterado) guardar(); }} placeholder="Escreva suas intenções para esta novena." />
        <span className="fd-aux">{texto.length}/{LIMITE_PEDIDOS} caracteres</span>
      </div>
      <div className="fd-linha-acoes" style={{ marginTop: 12 }}>
        <Botao variante="secundario" icone="check" onClick={guardar} disabled={!alterado}>Guardar pedidos</Botao>
        {pessoal.pedidos && <Botao variante="texto" icone="limpar" onClick={() => setConfirmar("pedidos")}>Apagar pedidos</Botao>}
      </div>
      {pessoal.falhouGravar && <div style={{ marginTop: 12 }}><Alerta tipo="erro" titulo="Não foi possível guardar">O armazenamento do navegador está cheio ou bloqueado.</Alerta></div>}

      <Confirmacao aberto={confirmar !== null}
        titulo={confirmar === "pedidos" ? "Apagar seus pedidos desta novena?" : "Limpar suas marcações desta novena?"}
        confirmar={confirmar === "pedidos" ? "Apagar pedidos" : "Limpar marcações"} cancelar="Manter"
        aoCancelar={() => setConfirmar(null)}
        aoConfirmar={() => {
          const ok = confirmar === "pedidos" ? pessoal.limparPedidos() : pessoal.limparMarcacoes();
          if (ok) avisar(confirmar === "pedidos" ? "Pedidos apagados deste dispositivo." : "Marcações removidas deste dispositivo.");
          setConfirmar(null);
        }}>
        <p>Eles estão guardados só neste dispositivo e não poderão ser recuperados.</p>
      </Confirmacao>
    </section>
  );
}

function ConteudoDoDia({ novenaId, numero }) {
  const c = useConsulta(`novena:${novenaId}:dia:${numero}`, (signal) => api.dia(novenaId, numero, { signal }));
  if (c.estado === "carregando") return <Carregando tipo="texto" quantidade={5} texto={`Carregando o dia ${numero}…`} />;
  if (c.estado === "erro") {
    if (ehNaoEncontrado(c.erro)) return <NaoEncontrado titulo={`Dia ${numero} não encontrado`} voltar={{ para: `/novenas/${novenaId}`, texto: "Voltar à novena" }} />;
    return <EstadoErro erro={c.erro} oQue={`o dia ${numero}`} aoTentar={c.recarregar} />;
  }
  const d = c.dados;
  return (
    <article aria-labelledby="dia-titulo">
      <p className="fd-rotulo">Dia {d.numero_dia} de {d.total_dias}{d.data ? ` · ${dataPorExtenso(d.data, { ano: false })}` : ""}</p>
      <h2 id="dia-titulo" className="fd-h2" style={{ marginTop: 4 }}>Reflexão do dia {d.numero_dia}</h2>
      <p className="fd-leitura fd-reflexao fd-texto-longo" style={{ marginTop: 16 }}>{d.texto_reflexao}</p>
      <h3 className="fd-h3" style={{ marginTop: 40, marginBottom: 12 }}>Orações do dia</h3>
      {d.oracoes.length === 0 ? <p className="fd-aux">Nenhuma oração base cadastrada para este dia.</p> : d.oracoes.map((o, i) => (
        <details key={o.id} className="fd-expansivel" open={i === 0}>
          <summary>{o.titulo}<Icone nome="baixo" /></summary>
          <div className="fd-expansivel__corpo"><p className="fd-texto-longo">{o.texto}</p></div>
        </details>
      ))}
      <nav className="fd-nav-dias" aria-label="Navegar entre os dias">
        {d.dia_anterior ? <BotaoLink variante="secundario" icone="esquerda" to={`/novenas/${novenaId}/dia/${d.dia_anterior}`}>Dia {d.dia_anterior}</BotaoLink> : <span />}
        {d.proximo_dia ? <BotaoLink variante="secundario" iconeDepois="direita" to={`/novenas/${novenaId}/dia/${d.proximo_dia}`}>Dia {d.proximo_dia}</BotaoLink> : <span />}
      </nav>
    </article>
  );
}

export default function Novena() {
  const { id: idBruto, numero: numeroBruto } = useParams();
  const id = lerId(idBruto);
  const numeroUrl = numeroBruto === undefined ? null : lerId(numeroBruto);
  const detalhe = useConsulta(`novena:${id}`, (signal) => api.detalhar(id, { signal }), { ativo: id !== null });
  const dias = useConsulta(`novena:${id}:dias`, (signal) => api.dias(id, { signal }), { ativo: id !== null });
  const novena = detalhe.estado === "sucesso" ? detalhe.dados : null;
  const totalDias = novena?.total_dias ?? 9;
  const pessoal = useNovenaPessoal(id ?? 0, totalDias);
  useTitulo(novena?.titulo ?? "Novena");

  const voltar = { para: "/novenas", texto: "Voltar às novenas" };
  if (id === null || (detalhe.estado === "erro" && ehNaoEncontrado(detalhe.erro))) {
    return <div className="fd-container fd-pagina"><NaoEncontrado titulo="Novena não encontrada" voltar={voltar} /></div>;
  }
  const numero = numeroUrl ?? (novena ? diaInicial(novena.agenda, totalDias) : null);
  const numeroValido = numero !== null && numero >= 1 && numero <= totalDias;

  return (
    <div className="fd-container fd-pagina">
      <Migalhas itens={[{ texto: "Início", para: "/" }, { texto: "Novenas", para: "/novenas" }, { texto: novena?.titulo ?? "Novena" }]} />
      {detalhe.estado === "carregando" && <Carregando tipo="texto" quantidade={4} texto="Carregando a novena…" />}
      {detalhe.estado === "erro" && <EstadoErro erro={detalhe.erro} oQue="esta novena" aoTentar={detalhe.recarregar} />}
      {novena && (
        <>
          <CabecalhoPagina titulo={novena.titulo} rotulo="Novena" lead={novena.descricao}>
            {novena.santo && <p style={{ marginTop: 12 }}><Link className="fd-link fd-link--vinho" to={`/santos/${novena.santo.id}`}>{novena.santo.nome}</Link></p>}
          </CabecalhoPagina>
          <Ornamento tipo="divisor" />
          <div className="fd-novena-topo">
            <AgendaDaNovena novena={novena} />
            {dias.estado === "carregando" && <Carregando quantidade={1} texto="Carregando o calendário…" />}
            {dias.estado === "erro" && <EstadoErro erro={dias.erro} oQue="o calendário da novena" aoTentar={dias.recarregar} />}
            {dias.estado === "sucesso" && (
              <section aria-labelledby="cal-titulo">
                <h2 id="cal-titulo" className="fd-h3">Os nove dias</h2>
                <CalendarioNovena novenaId={id} dias={dias.dados.dias} diaAtual={descreverAgenda(dias.dados.agenda, totalDias).diaAtual}
                  marcados={pessoal.marcados} selecionado={numeroValido ? numero : null} />
              </section>
            )}
          </div>
          <div className="fd-novena-dia">
            <div>
              {numeroValido ? <ConteudoDoDia novenaId={id} numero={numero} />
                : <NaoEncontrado titulo={`Dia ${numeroBruto} não encontrado`} voltar={{ para: `/novenas/${id}`, texto: "Voltar à novena" }} />}
            </div>
            {numeroValido && <div><NesteDispositivo novenaId={id} numero={numero} totalDias={totalDias} pessoal={pessoal} /></div>}
          </div>
        </>
      )}
    </div>
  );
}

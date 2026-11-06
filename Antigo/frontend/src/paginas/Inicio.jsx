import { Link } from "react-router-dom";
import { agenda as apiAgenda, santos as apiSantos, livros as apiLivros } from "../api/servicos.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { listarSantosAcessados } from "../estado/santosAcessados.js";
import { dataPorExtenso } from "../utils/datas.js";
import { lembrarIntervalo } from "../utils/intervalo.js";
import { MODULOS } from "../navegacao.js";
import { CabecalhoPagina, TituloSecao } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import Card from "../componentes/Card.jsx";
import CardSanto from "../componentes/CardSanto.jsx";
import Icone from "../componentes/Icone.jsx";
import { BotaoLink } from "../componentes/Botao.jsx";
import { Alerta, Carregando, EstadoErro } from "../componentes/Estados.jsx";

function NovenasDeHoje({ dados }) {
  if (dados.novenas_em_andamento.length === 0) {
    return (
      <Card simples titulo="Nenhuma novena em andamento hoje" nivel={3}>
        <p className="fd-card__corpo-texto">As novenas agendadas aparecem aqui no período em que estão sendo rezadas.</p>
        <p style={{ marginTop: 12 }}><Link className="fd-link" to="/novenas">Ver todas as novenas</Link></p>
      </Card>
    );
  }
  return (
    <div className="fd-pilha-cards">
      {dados.novenas_em_andamento.map((n) => (
        <Card key={n.agenda_id} destaque nivel={3} rotulo={`Em andamento · Dia ${n.dia_atual} de ${n.total_dias}`} titulo={n.novena.titulo}
          para={`/novenas/${n.novena.id}`} meta={n.novena.santo?.nome}
          acoes={<BotaoLink variante="especial" to={`/novenas/${n.novena.id}/dia/${n.dia_atual}`}>Ler o dia {n.dia_atual}</BotaoLink>} />
      ))}
    </div>
  );
}

function LiturgiaDeHoje({ dados }) {
  const l = dados.liturgia_dia;
  return (
    <Card nivel={3} rotulo="Liturgia do Dia" titulo={l?.santo_celebrado || "Liturgia do Dia"} para={`/liturgia?data=${dados.data}`}
      meta={dataPorExtenso(dados.data)}>
      {l ? (
        <ul className="fd-lista" style={{ marginTop: 16 }}>
          <li>Primeira Leitura</li><li>Salmo Responsorial</li>{l.segunda_leitura && <li>Segunda Leitura</li>}<li>Evangelho</li>
        </ul>
      ) : <p className="fd-card__corpo-texto">Não há liturgia cadastrada para hoje.</p>}
      {dados.liturgia_horas.length > 0 && (
        <p className="fd-card__corpo-texto fd-card__acima"><Link className="fd-link" to={`/liturgia/horas?data=${dados.data}`}>Liturgia das Horas: {dados.liturgia_horas.map((h) => h.bloco.nome).join(", ")}</Link></p>
      )}
    </Card>
  );
}

function SecaoHoje() {
  const c = useConsulta("agenda:hoje", (signal) => apiAgenda.doDia(undefined, { signal }).then((d) => { lembrarIntervalo(d.intervalo); return d; }));
  return (
    <section className="fd-secao" aria-labelledby="titulo-hoje">
      <TituloSecao id="titulo-hoje" titulo="Hoje" descricao={c.dados ? dataPorExtenso(c.dados.data) : null}
        acao={<Link className="fd-link" to="/agenda">Ver a agenda completa</Link>} />
      {c.estado === "carregando" && <Carregando quantidade={2} texto="Carregando a agenda de hoje…" />}
      {c.estado === "erro" && <EstadoErro erro={c.erro} oQue="a agenda de hoje" aoTentar={c.recarregar} />}
      {c.estado === "sucesso" && (
        <>
          <div className="fd-hoje">
            <div><h3 className="fd-h3" style={{ marginBottom: 16 }}>Novenas em andamento</h3><NovenasDeHoje dados={c.dados} /></div>
            <div><h3 className="fd-h3" style={{ marginBottom: 16 }}>Liturgia</h3><LiturgiaDeHoje dados={c.dados} /></div>
          </div>
          <div style={{ marginTop: 24 }}><Alerta tipo="aviso" titulo="Liturgia de demonstração" papel="note"><p>{c.dados.aviso}</p></Alerta></div>
        </>
      )}
    </section>
  );
}

function SecaoSantos() {
  const c = useConsulta("inicio:santos", (signal) => apiSantos.listar({ limite: 3 }, { signal }), { vazio: (p) => p.itens.length === 0 });
  if (c.estado === "vazio") return null;
  return (
    <section className="fd-secao" aria-labelledby="titulo-santos">
      <TituloSecao id="titulo-santos" titulo="Santos" descricao="Vidas, orações, novenas e livros de quem nos precede na fé."
        acao={<Link className="fd-link" to="/santos">Ver todos os santos</Link>} />
      {c.estado === "carregando" && <Carregando tipo="santos" quantidade={3} texto="Carregando santos…" />}
      {c.estado === "erro" && <EstadoErro erro={c.erro} oQue="os santos" aoTentar={c.recarregar} />}
      {c.estado === "sucesso" && <div className="fd-grade fd-grade--3">{c.dados.itens.map((s) => <CardSanto key={s.id} santo={s} />)}</div>}
    </section>
  );
}

function SecaoRecomendados() {
  const ids = listarSantosAcessados();
  const c = useConsulta(`inicio:recomendados:${ids.join(",")}`, (signal) => apiLivros.recomendados(ids, { limite: 3 }, { signal }), { ativo: ids.length > 0, vazio: (p) => p.itens.length === 0 });
  if (ids.length === 0 || c.estado === "vazio" || c.estado === "erro") return null;
  return (
    <section className="fd-secao" aria-labelledby="titulo-leituras">
      <TituloSecao id="titulo-leituras" titulo="Para continuar a leitura" descricao="Livros dos santos que você visitou neste dispositivo."
        acao={<Link className="fd-link" to="/livros">Ver livros</Link>} />
      {c.estado === "carregando" ? <Carregando quantidade={2} /> : (
        <div className="fd-grade fd-grade--3">
          {c.dados.itens.map((l) => <Card key={l.id} titulo={l.titulo} para={`/livros/${l.id}`} meta={[l.autor, l.santo?.nome].filter(Boolean).join(" · ")} rotulo="Recomendação de leitura" />)}
        </div>
      )}
    </section>
  );
}

export default function Inicio() {
  useTitulo(null);
  const atalhos = MODULOS.filter((m) => m.rota !== "/" && m.rota !== "/agenda");
  return (
    <div className="fd-container fd-pagina">
      <div className="fd-hero">
        <CabecalhoPagina ornamento="crista" titulo="Fides">
          <p className="fd-hero__lead">Santos, orações, novenas, livros e liturgia reunidos em um só lugar.</p>
          <div className="fd-linha-acoes fd-hero__acoes">
            <BotaoLink to="/santos">Conhecer os santos</BotaoLink>
            <BotaoLink variante="secundario" icone="oracoes" to="/oracoes">Ver orações</BotaoLink>
          </div>
        </CabecalhoPagina>
      </div>
      <Ornamento tipo="divisor" />
      <nav aria-label="Módulos do Fides">
        <ul className="fd-modulos">
          {atalhos.map((m) => <li key={m.rota}><Link className="fd-modulo" to={m.rota}><Icone nome={m.icone} />{m.nome}</Link></li>)}
        </ul>
      </nav>
      <SecaoHoje />
      <SecaoSantos />
      <SecaoRecomendados />
    </div>
  );
}

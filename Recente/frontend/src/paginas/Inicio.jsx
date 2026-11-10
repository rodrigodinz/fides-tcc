import { Link } from "react-router-dom";
import { servicoAgenda, servicoSantos, servicoLivros } from "../api/servicos.js";
import { useConsulta } from "../hooks/useConsulta.js";
import { useTitulo } from "../hooks/useTitulo.js";
import { listarSantosAcessados } from "../estado/santosAcessados.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { lembrarPeriodo } from "../utils/periodo.js";
import { Modulos } from "../navegacao.js";
import { CabecalhoPagina, TituloSecao } from "../componentes/Estrutura.jsx";
import Ornamento from "../componentes/Ornamento.jsx";
import Card from "../componentes/Card.jsx";
import CardSanto from "../componentes/CardSanto.jsx";
import Icone from "../componentes/Icone.jsx";
import { BotaoLink } from "../componentes/Botao.jsx";
import { Alerta, Carregando, EstadoErro } from "../componentes/Estados.jsx";

function NovenasDeHoje({ conteudosDoDia }) {
  if (conteudosDoDia.novenas_em_andamento.length === 0) {
    return (
      <Card simples titulo="Nenhuma novena em andamento hoje" nivel={3}>
        <p className="fd-card__corpo-texto">As novenas agendadas aparecem aqui no período em que estão sendo rezadas.</p>
        <p style={{ marginTop: 12 }}><Link className="fd-link" to="/novenas">Ver todas as novenas</Link></p>
      </Card>
    );
  }
  return (
    <div className="fd-pilha-cards">
      {conteudosDoDia.novenas_em_andamento.map((novenaEmAndamento) => (
        <Card key={novenaEmAndamento.agenda_id} destaque nivel={3}
          rotulo={`Em andamento · Dia ${novenaEmAndamento.dia_atual} de ${novenaEmAndamento.total_dias}`} titulo={novenaEmAndamento.novena.titulo}
          para={`/novenas/${novenaEmAndamento.novena.id}`} meta={novenaEmAndamento.novena.santo?.nome}
          acoes={<BotaoLink variante="especial" to={`/novenas/${novenaEmAndamento.novena.id}/dia/${novenaEmAndamento.dia_atual}`}>Ler o dia {novenaEmAndamento.dia_atual}</BotaoLink>} />
      ))}
    </div>
  );
}

function LiturgiaDeHoje({ conteudosDoDia }) {
  const liturgiaDoDia = conteudosDoDia.liturgia_do_dia;
  return (
    <Card nivel={3} rotulo="Liturgia do Dia" titulo={liturgiaDoDia?.santo_celebrado || "Liturgia do Dia"} para={`/liturgia?data=${conteudosDoDia.data}`}
      meta={escreverDataPorExtenso(conteudosDoDia.data)}>
      {liturgiaDoDia ? (
        <ul className="fd-lista" style={{ marginTop: 16 }}>
          <li>Primeira Leitura</li><li>Salmo Responsorial</li>{liturgiaDoDia.segunda_leitura && <li>Segunda Leitura</li>}<li>Evangelho</li>
        </ul>
      ) : <p className="fd-card__corpo-texto">Não há liturgia cadastrada para hoje.</p>}
      {conteudosDoDia.liturgia_das_horas.length > 0 && (
        <p className="fd-card__corpo-texto fd-card__acima">
          <Link className="fd-link" to={`/liturgia/horas?data=${conteudosDoDia.data}`}>
            Liturgia das Horas: {conteudosDoDia.liturgia_das_horas.map((hora) => hora.bloco.nome).join(", ")}
          </Link>
        </p>
      )}
    </Card>
  );
}

// bloco "Hoje": novenas em andamento e liturgia, vindos de GET /agenda
function SecaoHoje() {
  const consultaDeHoje = useConsulta("agenda:hoje", (signal) =>
    servicoAgenda.verConteudosDoDia(undefined, { signal }).then((conteudos) => { lembrarPeriodo(conteudos.periodo); return conteudos; }));
  return (
    <section className="fd-secao" aria-labelledby="titulo-hoje">
      <TituloSecao id="titulo-hoje" titulo="Hoje" descricao={consultaDeHoje.dados ? escreverDataPorExtenso(consultaDeHoje.dados.data) : null}
        acao={<Link className="fd-link" to="/agenda">Ver a agenda completa</Link>} />
      {consultaDeHoje.estado === "carregando" && <Carregando quantidade={2} texto="Carregando a agenda de hoje…" />}
      {consultaDeHoje.estado === "erro" && <EstadoErro erro={consultaDeHoje.erro} conteudoBuscado="a agenda de hoje" aoTentarNovamente={consultaDeHoje.recarregar} />}
      {consultaDeHoje.estado === "sucesso" && (
        <>
          <div className="fd-hoje">
            <div><h3 className="fd-h3" style={{ marginBottom: 16 }}>Novenas em andamento</h3><NovenasDeHoje conteudosDoDia={consultaDeHoje.dados} /></div>
            <div><h3 className="fd-h3" style={{ marginBottom: 16 }}>Liturgia</h3><LiturgiaDeHoje conteudosDoDia={consultaDeHoje.dados} /></div>
          </div>
          <div style={{ marginTop: 24 }}><Alerta tipo="aviso" titulo="Liturgia de demonstração" papel="note"><p>{consultaDeHoje.dados.aviso}</p></Alerta></div>
        </>
      )}
    </section>
  );
}

function SecaoSantos() {
  const consultaDeSantos = useConsulta("inicio:santos", (signal) => servicoSantos.listarSantos({ limite: 3 }, { signal }),
    { verificarSeVazio: (pagina) => pagina.itens.length === 0 });
  if (consultaDeSantos.estado === "vazio") return null;
  return (
    <section className="fd-secao" aria-labelledby="titulo-santos">
      <TituloSecao id="titulo-santos" titulo="Santos" descricao="Vidas, orações, novenas e livros de quem nos precede na fé."
        acao={<Link className="fd-link" to="/santos">Ver todos os santos</Link>} />
      {consultaDeSantos.estado === "carregando" && <Carregando tipo="santos" quantidade={3} texto="Carregando santos…" />}
      {consultaDeSantos.estado === "erro" && <EstadoErro erro={consultaDeSantos.erro} conteudoBuscado="os santos" aoTentarNovamente={consultaDeSantos.recarregar} />}
      {consultaDeSantos.estado === "sucesso" && (
        <div className="fd-grade fd-grade--3">{consultaDeSantos.dados.itens.map((santo) => <CardSanto key={santo.id} santo={santo} />)}</div>
      )}
    </section>
  );
}

// só aparece se a pessoa já visitou algum santo neste aparelho
function SecaoRecomendados() {
  const idsDosSantosAcessados = listarSantosAcessados();
  const consultaDeRecomendados = useConsulta(`inicio:recomendados:${idsDosSantosAcessados.join(",")}`,
    (signal) => servicoLivros.listarLivrosRecomendados(idsDosSantosAcessados, { limite: 3 }, { signal }),
    { consultaAtiva: idsDosSantosAcessados.length > 0, verificarSeVazio: (pagina) => pagina.itens.length === 0 });
  if (idsDosSantosAcessados.length === 0 || consultaDeRecomendados.estado === "vazio" || consultaDeRecomendados.estado === "erro") return null;
  return (
    <section className="fd-secao" aria-labelledby="titulo-leituras">
      <TituloSecao id="titulo-leituras" titulo="Para continuar a leitura" descricao="Livros dos santos que você visitou neste dispositivo."
        acao={<Link className="fd-link" to="/livros">Ver livros</Link>} />
      {consultaDeRecomendados.estado === "carregando" ? <Carregando quantidade={2} /> : (
        <div className="fd-grade fd-grade--3">
          {consultaDeRecomendados.dados.itens.map((livro) => (
            <Card key={livro.id} titulo={livro.titulo} para={`/livros/${livro.id}`} meta={[livro.autor, livro.santo?.nome].filter(Boolean).join(" · ")} rotulo="Recomendação de leitura" />
          ))}
        </div>
      )}
    </section>
  );
}

// Página inicial: apresentação, atalhos dos módulos e as seções abaixo.
export default function Inicio() {
  useTitulo(null);
  const atalhosDosModulos = Modulos.filter((modulo) => modulo.rota !== "/" && modulo.rota !== "/agenda");
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
          {atalhosDosModulos.map((modulo) => <li key={modulo.rota}><Link className="fd-modulo" to={modulo.rota}><Icone nome={modulo.icone} />{modulo.nome}</Link></li>)}
        </ul>
      </nav>
      <SecaoHoje />
      <SecaoSantos />
      <SecaoRecomendados />
    </div>
  );
}

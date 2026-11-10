// Página da novena (novena.html?id=1 para o dia atual (O id é 1) ou novena.html?id=1&dia=3 para o dia 3, e assim por diante)
import { montarLayout, definirTitulo, avisar, pedirConfirmacao } from "../layout.js";
import { servicoNovenas } from "../api/servicos.js";
import { ehErroDeNaoEncontrado } from "../api/erros.js";
import { criarConsulta } from "../utils/consulta.js";
import { lerParametrosDaUrl } from "../utils/url.js";
import { lerIdDaUrl } from "../utils/paginacao.js";
import { enderecos } from "../utils/enderecos.js";
import { escreverDataPorExtenso } from "../utils/datas.js";
import { descreverAgendaDaNovena, escolherDiaInicial } from "../utils/novena.js";
import { armazenamentoDisponivel } from "../estado/armazenamento.js";
import { alternarDiaMarcado, lerNovenaPessoal, salvarNovenaPessoal, Limite_De_Caracteres_Dos_Pedidos } from "../estado/novenaPessoal.js";
import { escaparHtml } from "../componentes/html.js";
import { icone } from "../componentes/icones.js";
import {
  alerta, botao, botaoLink, cabecalhoDaPagina, calendarioDaNovena, carregando, mensagemDeErro, ligarTentarNovamente, caminhoDeNavegacao,
  mensagemDeNaoEncontrado, ornamento,
} from "../componentes/componentes.js";

montarLayout();

const paginaDaNovena = document.getElementById("pagina-da-novena");
const parametrosDaUrl = lerParametrosDaUrl();
const novenaId = lerIdDaUrl(parametrosDaUrl.get("id"));
const numeroEscritoNaUrl = parametrosDaUrl.get("dia");
const numeroDoDiaNaUrl = numeroEscritoNaUrl === null ? null : lerIdDaUrl(numeroEscritoNaUrl);
const voltarParaNovenas = { para: enderecos.novenas(), texto: "Voltar às novenas" };

// estado da página
let novena = null;
let numeroDoDia = null;
let diasDaNovena = null;  // resposta de GET /novenas/{id}/dias
let dadosPessoais = { marcados: [], pedidos: "" };
let falhouAoGravar = false;

const montarCaminhoDeNavegacao = (tituloDaNovena) => caminhoDeNavegacao([
  { texto: "Início", para: enderecos.inicio() }, { texto: "Novenas", para: enderecos.novenas() }, { texto: tituloDaNovena ?? "Novena" },
]);

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- quadro da agenda +-+-+-+-+-+-+-+-+-+-+-+-+-+-
const Classes_Das_Situacoes = {
  em_andamento: "situacao-em-andamento",
  agendada: "situacao-agendada",
  sem_agenda: "situacao-sem-agenda",
};

// situação (em andamento, agendada ou não agendada) da novena, o período e o dia X de 9
function desenharAgendaDaNovena() {
  const situacaoDaAgenda = descreverAgendaDaNovena(novena.agenda, novena.total_dias);
  const agenda = novena.agenda;
  const periodo = agenda
    ? `<p class="texto-auxiliar" style="margin-top:4px">De ${escreverDataPorExtenso(agenda.data_inicio, { comDiaDaSemana: false })} a ${escreverDataPorExtenso(agenda.data_fim, { comDiaDaSemana: false })}</p>`
    : "";
  const destaqueDoDia = situacaoDaAgenda.tipo === "em_andamento"
    ? `<p class="dia-atual-em-destaque" aria-label="${situacaoDaAgenda.texto}"><small>Dia</small>${agenda.dia_atual}<small>de ${novena.total_dias}</small></p>`
    : `<p class="subtitulo-menor" style="color:var(--azul-profundo)">${escaparHtml(situacaoDaAgenda.tipo === "agendada" ? situacaoDaAgenda.texto : "Sem agenda ativa")}</p>`;
  const explicacao = situacaoDaAgenda.tipo === "sem_agenda"
    ? "Os nove dias podem ser lidos livremente; não há datas definidas."
    : "O dia atual segue a agenda da novena e é o mesmo para todos. Você pode ler qualquer dia.";
  return '<section class="card card-simples" aria-labelledby="titulo-da-agenda"><div class="resumo-da-agenda"><div>'
    + '<h2 id="titulo-da-agenda" class="rotulo-pequeno">Agenda da novena</h2>'
    + `<p class="situacao ${Classes_Das_Situacoes[situacaoDaAgenda.tipo]}" style="margin-top:6px">${situacaoDaAgenda.rotulo}</p>${periodo}</div>`
    + `${destaqueDoDia}</div><p class="texto-auxiliar" style="margin-top:12px">${explicacao}</p></section>`;
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- calendário dos nove dias +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// A Alexandra deu a ideia de fazer por uma API externa, mas deixa isso pra fase 2, por enquanto eu achei essa forma de fazer um calendário por js mesmo K
function desenharCalendario() {
  const areaDoCalendario = document.getElementById("calendario-da-novena");
  areaDoCalendario.innerHTML = '<section aria-labelledby="titulo-do-calendario"><h2 id="titulo-do-calendario" class="subtitulo">Os nove dias</h2>'
    + calendarioDaNovena({
      novenaId, dias: diasDaNovena.dias,
      diaAtual: descreverAgendaDaNovena(diasDaNovena.agenda, novena.total_dias).diaAtual,
      marcados: dadosPessoais.marcados, diaSelecionado: numeroDoDiaValido() ? numeroDoDia : null,
    })
    + "</section>";
}

async function carregarCalendario() {
  const areaDoCalendario = document.getElementById("calendario-da-novena");
  areaDoCalendario.innerHTML = carregando({ quantidade: 1, texto: "Carregando o calendário…" });
  const resultado = await criarConsulta()((signal) => servicoNovenas.listarDiasDaNovena(novenaId, { signal }));
  if (resultado.estado === "erro") {
    areaDoCalendario.innerHTML = mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "o calendário da novena" });
    ligarTentarNovamente(areaDoCalendario, carregarCalendario);
    return;
  }
  diasDaNovena = resultado.dados;
  desenharCalendario();
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- conteúdo do dia +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// reflexão e orações do dia (GET /novenas/{id}/dias/{n})
async function carregarConteudoDoDia() {
  const areaDoDia = document.getElementById("conteudo-do-dia");
  areaDoDia.innerHTML = carregando({ tipo: "texto", quantidade: 5, texto: `Carregando o dia ${numeroDoDia}…` });
  const resultado = await criarConsulta()((signal) => servicoNovenas.verDiaDaNovena(novenaId, numeroDoDia, { signal }));
  if (resultado.estado === "erro") {
    if (ehErroDeNaoEncontrado(resultado.erro)) {
      areaDoDia.innerHTML = mensagemDeNaoEncontrado({ titulo: `Dia ${numeroDoDia} não encontrado`, voltar: { para: enderecos.novena(novenaId), texto: "Voltar à novena" } });
      return;
    }
    areaDoDia.innerHTML = mensagemDeErro({ erro: resultado.erro, conteudoBuscado: `o dia ${numeroDoDia}` });
    ligarTentarNovamente(areaDoDia, carregarConteudoDoDia);
    return;
  }
  const diaDaNovena = resultado.dados;
  // <details> (caixa que abre e fecha sozinha)
  const oracoesDoDia = diaDaNovena.oracoes.length === 0
    ? '<p class="texto-auxiliar">Nenhuma oração base cadastrada para este dia.</p>'
    : diaDaNovena.oracoes.map((oracao, posicao) =>
      `<details class="secao-expansivel"${posicao === 0 ? " open" : ""}><summary>${escaparHtml(oracao.titulo)}${icone("baixo")}</summary><div class="conteudo-da-secao-expansivel"><p class="texto-com-quebras-de-linha">${escaparHtml(oracao.texto)}</p></div></details>`).join("");
  const diaAnterior = diaDaNovena.dia_anterior
    ? botaoLink({ variante: "secundario", icone: "esquerda", texto: `Dia ${diaDaNovena.dia_anterior}`, para: enderecos.novena(novenaId, diaDaNovena.dia_anterior) })
    : "<span></span>";
  const proximoDia = diaDaNovena.proximo_dia
    ? botaoLink({ variante: "secundario", iconeDepois: "direita", texto: `Dia ${diaDaNovena.proximo_dia}`, para: enderecos.novena(novenaId, diaDaNovena.proximo_dia) })
    : "<span></span>";
  areaDoDia.innerHTML = '<article aria-labelledby="titulo-do-dia">'
    + `<p class="rotulo-pequeno">Dia ${diaDaNovena.numero_do_dia} de ${diaDaNovena.total_dias}${diaDaNovena.data ? ` · ${escreverDataPorExtenso(diaDaNovena.data, { comAno: false })}` : ""}</p>`
    + `<h2 id="titulo-do-dia" class="titulo-de-secao" style="margin-top:4px">Reflexão do dia ${diaDaNovena.numero_do_dia}</h2>`
    + `<p class="largura-de-leitura texto-de-reflexao texto-com-quebras-de-linha" style="margin-top:16px">${escaparHtml(diaDaNovena.texto_reflexao)}</p>`
    + '<h3 class="subtitulo" style="margin-top:40px;margin-bottom:12px">Orações do dia</h3>'
    + oracoesDoDia
    + `<nav class="navegacao-entre-os-dias" aria-label="Navegar entre os dias">${diaAnterior}${proximoDia}</nav>`
    + "</article>";
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- neste dispositivo +-+-+-+-+-+-+-+-+-+-+-+-+-+-
// Parte pessoal (marca o dia da novena que já foi rezado e escreve os pedidos, esse conteúdo inclusive fica só no navegador (localStorage)
function guardarNoDispositivo(novosDados) {
  const { gravou, dados } = salvarNovenaPessoal(novenaId, novosDados, novena.total_dias);
  dadosPessoais = dados;
  falhouAoGravar = !gravou;
  desenharNesteDispositivo();
  if (diasDaNovena) desenharCalendario();  // o calendário mostra os dias marcados
  return gravou;
}

function desenharNesteDispositivo() {
  const area = document.getElementById("neste-dispositivo");
  if (!armazenamentoDisponivel()) {
    area.innerHTML = alerta({
      tipo: "aviso", titulo: "Marcações e pedidos indisponíveis", papel: "note",
      corpo: "<p>Este navegador não permite guardar dados no dispositivo (por exemplo, em navegação privada). O conteúdo da novena continua disponível.</p>",
    });
    return;
  }
  // lembra qual controle estava focado para devolver o foco depois de redesenhar
  const chaveFocada = area.contains(document.activeElement) ? document.activeElement.dataset.chave : null;
  const diaMarcado = dadosPessoais.marcados.includes(numeroDoDia);
  area.innerHTML = '<section class="area-pessoal" aria-labelledby="titulo-da-area-pessoal">'
    + `<h2 id="titulo-da-area-pessoal" class="subtitulo-menor" style="display:flex;gap:10px;align-items:center">${icone("dispositivo")}Neste dispositivo</h2>`
    + '<p class="texto-auxiliar" style="margin-top:6px">Suas marcações e pedidos ficam só neste aparelho. Não são enviados e não mudam o dia da agenda.</p>'
    + `<label class="marcar-como-rezado" style="margin-top:16px"><input type="checkbox" data-chave="marcar"${diaMarcado ? " checked" : ""}>Rezei o dia ${numeroDoDia}</label>`
    + `<p class="texto-auxiliar">Você marcou ${dadosPessoais.marcados.length} de ${novena.total_dias} dias.</p>`
    + (dadosPessoais.marcados.length > 0 ? botao({ variante: "texto", pequeno: true, texto: "Limpar marcações", atributos: 'data-chave="limpar-marcacoes"' }) : "")
    + '<div class="campo-de-formulario" style="margin-top:20px"><label for="pedidos">Meus pedidos</label>'
    + `<textarea id="pedidos" class="area-de-texto" maxlength="${Limite_De_Caracteres_Dos_Pedidos}" placeholder="Escreva suas intenções para esta novena." data-chave="pedidos">${escaparHtml(dadosPessoais.pedidos)}</textarea>`
    + `<span class="texto-auxiliar" data-contador>${dadosPessoais.pedidos.length}/${Limite_De_Caracteres_Dos_Pedidos} caracteres</span></div>`
    + '<div class="linha-de-botoes" style="margin-top:12px">'
    + botao({ variante: "secundario", icone: "check", texto: "Guardar pedidos", atributos: 'data-chave="guardar" disabled' })
    + (dadosPessoais.pedidos ? botao({ variante: "texto", icone: "limpar", texto: "Apagar pedidos", atributos: 'data-chave="apagar"' }) : "")
    + "</div>"
    + (falhouAoGravar ? `<div style="margin-top:12px">${alerta({ tipo: "erro", titulo: "Não foi possível guardar", corpo: "O armazenamento do navegador está cheio ou bloqueado." })}</div>` : "")
    + "</section>";
  ligarNesteDispositivo(area);
  if (chaveFocada) area.querySelector(`[data-chave="${chaveFocada}"]`)?.focus();
}

function ligarNesteDispositivo(area) {
  const caixaRezei = area.querySelector('[data-chave="marcar"]');
  const campoDosPedidos = area.querySelector('[data-chave="pedidos"]');
  const contador = area.querySelector("[data-contador]");
  const botaoGuardar = area.querySelector('[data-chave="guardar"]');
  const pedidosForamAlterados = () => campoDosPedidos.value !== dadosPessoais.pedidos;
  // junta o que já está guardado com o texto que está no campo agora
  const dadosComPedidosDigitados = () => ({ ...dadosPessoais, pedidos: campoDosPedidos.value });

  caixaRezei.addEventListener("change", () => {
    const diaEstavaMarcado = dadosPessoais.marcados.includes(numeroDoDia);
    if (guardarNoDispositivo(alternarDiaMarcado(dadosComPedidosDigitados(), numeroDoDia))) {
      avisar(diaEstavaMarcado ? `Marcação do dia ${numeroDoDia} removida.` : `Dia ${numeroDoDia} marcado como rezado neste dispositivo.`);
    }
  });
  // enquanto digita, só atualiza o contador e o botão
  campoDosPedidos.addEventListener("input", () => {
    contador.textContent = `${campoDosPedidos.value.length}/${Limite_De_Caracteres_Dos_Pedidos} caracteres`;
    botaoGuardar.disabled = !pedidosForamAlterados();
  });
  const guardarPedidos = () => {
    if (guardarNoDispositivo(dadosComPedidosDigitados())) avisar("Pedidos guardados neste dispositivo.");
  };
  // ao sair do campo, guarda automaticamente se mudou
  campoDosPedidos.addEventListener("blur", (evento) => {
    if (pedidosForamAlterados() && !area.contains(evento.relatedTarget)) guardarPedidos();
  });
  botaoGuardar.addEventListener("click", guardarPedidos);

  area.querySelector('[data-chave="limpar-marcacoes"]')?.addEventListener("click", async () => {
    const confirmou = await pedirConfirmacao({
      titulo: "Limpar suas marcações desta novena?", texto: "Eles estão guardados só neste dispositivo e não poderão ser recuperados.",
      textoConfirmar: "Limpar marcações", textoCancelar: "Manter",
    });
    if (confirmou && guardarNoDispositivo({ ...dadosComPedidosDigitados(), marcados: [] })) avisar("Marcações removidas deste dispositivo.");
  });
  area.querySelector('[data-chave="apagar"]')?.addEventListener("click", async () => {
    const confirmou = await pedirConfirmacao({
      titulo: "Apagar seus pedidos desta novena?", texto: "Eles estão guardados só neste dispositivo e não poderão ser recuperados.",
      textoConfirmar: "Apagar pedidos", textoCancelar: "Manter",
    });
    if (confirmou && guardarNoDispositivo({ ...dadosPessoais, pedidos: "" })) avisar("Pedidos apagados deste dispositivo.");
  });
}

// +-+-+-+-+-+-+-+-+-+-+-+-+-+- montagem da página +-+-+-+-+-+-+-+-+-+-+-+-+-+-
const numeroDoDiaValido = () => numeroDoDia !== null && numeroDoDia >= 1 && numeroDoDia <= novena.total_dias;

function desenharNovena() {
  const linkDoSanto = novena.santo
    ? `<p style="margin-top:12px"><a class="link link-vinho" href="${enderecos.santo(novena.santo.id)}">${escaparHtml(novena.santo.nome)}</a></p>`
    : "";
  paginaDaNovena.innerHTML = montarCaminhoDeNavegacao(novena.titulo)
    + cabecalhoDaPagina({ titulo: novena.titulo, rotulo: "Novena", textoDeAbertura: novena.descricao, extra: linkDoSanto })
    + ornamento("divisor")
    + `<div class="topo-da-pagina-da-novena">${desenharAgendaDaNovena()}<div id="calendario-da-novena"></div></div>`
    + '<div class="conteudo-do-dia-da-novena"><div id="conteudo-do-dia"></div>'
    + (numeroDoDiaValido() ? '<div id="neste-dispositivo"></div>' : "")
    + "</div>";

  if (numeroDoDiaValido()) {
    desenharNesteDispositivo();
    carregarConteudoDoDia();
  } else {
    document.getElementById("conteudo-do-dia").innerHTML = mensagemDeNaoEncontrado({
      titulo: `Dia ${numeroEscritoNaUrl} não encontrado`, voltar: { para: enderecos.novena(novenaId), texto: "Voltar à novena" },
    });
  }
  carregarCalendario();
}

async function carregarNovena() {
  if (novenaId === null) {
    paginaDaNovena.innerHTML = mensagemDeNaoEncontrado({ titulo: "Novena não encontrada", voltar: voltarParaNovenas });
    return;
  }
  paginaDaNovena.innerHTML = montarCaminhoDeNavegacao() + carregando({ tipo: "texto", quantidade: 4, texto: "Carregando a novena…" });
  const resultado = await criarConsulta()((signal) => servicoNovenas.detalharNovena(novenaId, { signal }));
  if (resultado.estado === "erro") {
    if (ehErroDeNaoEncontrado(resultado.erro)) {
      paginaDaNovena.innerHTML = mensagemDeNaoEncontrado({ titulo: "Novena não encontrada", voltar: voltarParaNovenas });
      return;
    }
    paginaDaNovena.innerHTML = montarCaminhoDeNavegacao() + mensagemDeErro({ erro: resultado.erro, conteudoBuscado: "esta novena" });
    ligarTentarNovamente(paginaDaNovena, carregarNovena);
    return;
  }
  novena = resultado.dados;
  definirTitulo(novena.titulo);
  // sem ?dia= na URL abre no dia atual da agenda (ou no dia 1)
  numeroDoDia = numeroDoDiaNaUrl ?? escolherDiaInicial(novena.agenda, novena.total_dias);
  dadosPessoais = lerNovenaPessoal(novenaId, novena.total_dias);
  desenharNovena();
}

carregarNovena();

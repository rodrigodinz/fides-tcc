/** Mensagens amigáveis por código de erro. Nunca mostram detalhes internos. */
const RECUPERAVEIS = new Set(["FALHA_DE_REDE", "TEMPO_ESGOTADO", "ERRO_INTERNO", "SERVICO_INDISPONIVEL"]);

export function ehRecuperavel(erro) {
  return RECUPERAVEIS.has(erro?.codigo) || !erro?.codigo;
}

export function ehNaoEncontrado(erro) {
  return erro?.codigo === "RECURSO_NAO_ENCONTRADO" || erro?.codigo === "ROTA_NAO_ENCONTRADA";
}

/** @param {string} oQue ex.: "as orações" */
export function mensagemErro(erro, oQue = "o conteúdo") {
  switch (erro?.codigo) {
    case "FALHA_DE_REDE":
      return { titulo: `Não foi possível carregar ${oQue} no momento.`, texto: "Verifique sua conexão e tente novamente." };
    case "TEMPO_ESGOTADO":
      return { titulo: `Não foi possível carregar ${oQue} a tempo.`, texto: "O servidor demorou para responder. Tente novamente." };
    case "SERVICO_INDISPONIVEL":
    case "ERRO_INTERNO":
      return { titulo: "O serviço está indisponível no momento.", texto: "Tente novamente em instantes." };
    case "PARAMETRO_INVALIDO":
      return { titulo: "Algum filtro informado não é válido.", texto: "Limpe os filtros e tente de novo." };
    case "DATA_FORA_DO_INTERVALO":
      return { titulo: "Data fora do período disponível.", texto: "Nesta versão de demonstração só há conteúdo de uma semana antes a uma semana depois de hoje." };
    case "LITURGIA_NAO_CADASTRADA":
      return { titulo: "Ainda não há liturgia cadastrada para esta data.", texto: "Escolha outra data dentro do período disponível." };
    case "RECURSO_NAO_ENCONTRADO":
    case "ROTA_NAO_ENCONTRADA":
      return { titulo: "Conteúdo não encontrado.", texto: "O endereço pode estar incorreto ou o conteúdo não existe mais." };
    default:
      return { titulo: `Não foi possível carregar ${oQue} no momento.`, texto: "Tente novamente." };
  }
}

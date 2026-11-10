from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Santo

from ..errors import erro_recurso_nao_encontrado
from ..schemas.comum import Pagina
from ..schemas.santos import DetalhesDoSanto, LivroDoSanto, NovenaDoSanto, OracaoDoSanto, ResumoDoSanto
from .busca import escapar_caracteres_do_like, normalizar_texto_da_busca
from .paginacao import ParametrosDePaginacao, montar_pagina_vazia, paginar


def listar_santos(session: Session, parametros: ParametrosDePaginacao,
                  nome: str | None) -> Pagina[ResumoDoSanto]:
    consulta = select(Santo)
    if nome is not None and nome.strip():
        nome_buscado = normalizar_texto_da_busca(nome)
        if not nome_buscado:
            return montar_pagina_vazia(parametros)
        consulta = consulta.where(
            Santo.nome_busca.like(f"%{escapar_caracteres_do_like(nome_buscado)}%", escape="\\"))
    consulta = consulta.order_by(Santo.nome, Santo.id)
    return paginar(session, consulta, parametros, ResumoDoSanto.model_validate)


def detalhar_santo(session: Session, santo_id: int) -> DetalhesDoSanto:
    santo = Santo.buscar_por_id(session, santo_id)
    if santo is None:
        raise erro_recurso_nao_encontrado("Santo")
    return DetalhesDoSanto(
        id=santo.id, nome=santo.nome, foto_url=santo.foto_url, biografia=santo.biografia,
        oracoes=[OracaoDoSanto(id=oracao.id, titulo=oracao.titulo, basica=oracao.basica)
                 for oracao in santo.ver_oracao_santo()],
        novenas=[NovenaDoSanto(id=novena.id, titulo=novena.titulo, descricao=novena.descricao)
                 for novena in santo.ver_novena_santo()],
        livros=[LivroDoSanto(id=livro.id, titulo=livro.titulo, autor=livro.autor)
                for livro in santo.ver_livro_santo()],
    )

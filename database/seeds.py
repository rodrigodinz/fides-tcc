"""Seeds iniciais do FIDES.

Uso (a partir da raiz do repositório):

    python -m database.seeds                          # cria tabelas (se faltarem) e popula
    python -m database.seeds --redefinir-senha-admin  # idem, e regrava a senha do admin
    python -m database.seeds --reset                  # DESTRUTIVO: apaga TODAS as tabelas e dados

Política dos seeds
------------------
* Criação de tabelas e inserção de dados são etapas distintas
  (``criar_tabelas()`` x ``executar_seeds()``).
* Idempotentes: registros já existentes não são duplicados nem recriados.
* Atualizações controladas (as ÚNICAS que alteram registros existentes):
    1. ``Oracao.basica`` é alinhada às listas ORACOES_BASICAS / ORACOES_COMPLEMENTARES;
    2. o santo gravado como "Santa Teresa de Ávila" (grafia da versão anterior) é
       renomeado para "Santa Teresa d'Ávila" (mesmo registro, sem duplicar), e o
       autor do livro correspondente acompanha;
    3. administrador da versão anterior (sem login) recebe o login configurado,
       mantendo a senha que já possuía.
* Associações a momentos do dia só são ACRESCENTADAS, nunca removidas.
* Tudo roda em uma única transação: se algo falhar, nada é gravado (rollback).
* O conteúdo religioso é inicial e deve ser revisado/ampliado pelo painel
  administrativo (US18-US22).

Variáveis de ambiente (opcionais):
    FIDES_ADMIN_LOGIN     login do administrador (padrão de desenvolvimento: "adm")
    FIDES_ADMIN_SENHA     senha do administrador (nome principal)
    FIDES_ADMIN_PASSWORD  alias de compatibilidade; só vale se FIDES_ADMIN_SENHA
                          não estiver definida
    FIDES_ADMIN_EMAIL     e-mail opcional do administrador (também aceito no login)
"""
import argparse
import os
import warnings

from sqlalchemy import inspect, select, text

from .connection import DATABASE_URL, SessionLocal, apagar_tabelas, criar_tabelas
from .models import (
    Administrador,
    BlocoMomento,
    Livro,
    MomentoDia,
    Novena,
    Oracao,
    Santo,
)

LOGIN_PADRAO_DEV = "adm"
SENHA_PADRAO_DEV = "senha"  # SOMENTE desenvolvimento/MVP; troque antes de publicar.

# --------------------------------------------------------------------------- #
# Conteúdo
# --------------------------------------------------------------------------- #
# Orações BÁSICAS do catálogo (oração geral, sem santo). Textos preservados.
ORACOES_BASICAS = [
    {
        "titulo": "Pai Nosso",
        "texto": (
            "Pai nosso, que estais nos céus, santificado seja o vosso nome, venha a nós o "
            "vosso reino, seja feita a vossa vontade, assim na terra como no céu. O pão "
            "nosso de cada dia nos dai hoje, perdoai-nos as nossas ofensas, assim como nós "
            "perdoamos a quem nos tem ofendido, e não nos deixeis cair em tentação, mas "
            "livrai-nos do mal. Amém."
        ),
        "momentos": [BlocoMomento.AO_ACORDAR, BlocoMomento.ANTES_DE_DORMIR],
    },
    {
        "titulo": "Ave Maria",
        "texto": (
            "Ave Maria, cheia de graça, o Senhor é convosco, bendita sois vós entre as "
            "mulheres e bendito é o fruto do vosso ventre, Jesus. Santa Maria, Mãe de Deus, "
            "rogai por nós, pecadores, agora e na hora de nossa morte. Amém."
        ),
        "momentos": [BlocoMomento.AO_ACORDAR, BlocoMomento.ANTES_DE_DORMIR],
    },
    {
        "titulo": "Glória ao Pai",
        "texto": (
            "Glória ao Pai, ao Filho e ao Espírito Santo, como era no princípio, agora e "
            "sempre, e pelos séculos dos séculos. Amém."
        ),
        "momentos": [],
    },
    {
        "titulo": "Credo",
        "texto": (
            "Creio em Deus Pai todo-poderoso, Criador do céu e da terra. E em Jesus Cristo, "
            "seu único Filho, nosso Senhor, que foi concebido pelo poder do Espírito Santo, "
            "nasceu da Virgem Maria, padeceu sob Pôncio Pilatos, foi crucificado, morto e "
            "sepultado; desceu à mansão dos mortos; ressuscitou ao terceiro dia; subiu aos "
            "céus, está sentado à direita de Deus Pai todo-poderoso, donde há de vir a julgar "
            "os vivos e os mortos. Creio no Espírito Santo, na santa Igreja Católica, na "
            "comunhão dos santos, na remissão dos pecados, na ressurreição da carne, na vida "
            "eterna. Amém."
        ),
        "momentos": [BlocoMomento.MISSA],
    },
    {
        "titulo": "Santo Anjo",
        "texto": (
            "Santo Anjo do Senhor, meu zeloso guardador, se a ti me confiou a piedade divina, "
            "sempre me rege, guarda, governa e ilumina. Amém."
        ),
        "momentos": [BlocoMomento.ANTES_DE_DORMIR],
    },
]

# Orações COMPLEMENTARES (gerais, não básicas). Textos existentes preservados.
ORACOES_COMPLEMENTARES = [
    {
        "titulo": "Invocação ao Espírito Santo",
        "texto": (
            "Vinde, Espírito Santo, enchei os corações dos vossos fiéis e acendei neles o "
            "fogo do vosso amor. Enviai o vosso Espírito e tudo será criado, e renovareis a "
            "face da terra. Oremos: Ó Deus, que instruístes os corações dos vossos fiéis com "
            "a luz do Espírito Santo, concedei-nos que, no mesmo Espírito, apreciemos o que "
            "é reto e gozemos sempre da sua consolação. Por Cristo, Senhor nosso. Amém."
        ),
        "momentos": [BlocoMomento.AO_ACORDAR],
    },
    {
        # Começo exigido: "São Miguel Arcanjo, defendei-nos no combate..." (conferido em
        # fontes católicas). O trecho final é a forma tradicional breve atribuída a
        # Leão XIII e deve ser revisado pelo desenvolvedor (ver relatório).
        "titulo": "Oração a São Miguel Arcanjo",
        "texto": (
            "São Miguel Arcanjo, defendei-nos no combate, sede o nosso refúgio contra as "
            "maldades e ciladas do demônio. Ordene-lhe Deus, instantemente o pedimos, e vós, "
            "príncipe da milícia celeste, pela virtude divina, precipitai no inferno a "
            "satanás e a todos os espíritos malignos, que andam pelo mundo para perder as "
            "almas. Amém."
        ),
        "momentos": [],
    },
    {
        "titulo": "Oferecimento do dia",
        "texto": (
            "Divino Coração de Jesus, eu vos ofereço, por meio do Coração Imaculado de Maria, "
            "as orações, obras, alegrias e sofrimentos deste dia, em reparação dos pecados e "
            "por todas as intenções pelas quais vos imolais continuamente no Santo Sacrifício "
            "do altar. Amém."
        ),
        "momentos": [BlocoMomento.AO_ACORDAR],
    },
    {
        "titulo": "Bênção da refeição",
        "texto": (
            "Abençoai-nos, Senhor, a nós e a estes dons que da vossa bondade vamos receber. "
            "Por Cristo, Senhor nosso. Amém."
        ),
        "momentos": [BlocoMomento.REFEICOES],
    },
    {
        "titulo": "Alma de Cristo",
        "texto": (
            "Alma de Cristo, santificai-me. Corpo de Cristo, salvai-me. Sangue de Cristo, "
            "inebriai-me. Água do lado de Cristo, lavai-me. Paixão de Cristo, confortai-me. "
            "Ó bom Jesus, ouvi-me. Dentro de vossas chagas, escondei-me. Não permitais que "
            "eu me separe de vós. Do espírito maligno, defendei-me. Na hora da minha morte, "
            "chamai-me. E mandai-me ir para vós, para que com os vossos santos vos louve. "
            "Pelos séculos dos séculos. Amém."
        ),
        "momentos": [BlocoMomento.MISSA],
    },
]

SANTOS = [
    {
        "nome": "São Tomás de Aquino",
        "foto_url": "/static/santos/tomas-de-aquino.jpg",
        "biografia": (
            "Frade dominicano italiano (c. 1225–1274), teólogo e Doutor da Igreja. Autor da "
            "Suma Teológica, uniu fé e razão em uma síntese que influencia a teologia até hoje. "
            "Sua memória litúrgica é celebrada em 28 de janeiro."
        ),
    },
    {
        "nome": "Santa Teresinha do Menino Jesus",
        "foto_url": "/static/santos/teresinha.jpg",
        "biografia": (
            "Teresa de Lisieux (1873–1897), religiosa carmelita francesa que viveu o 'pequeno "
            "caminho' da confiança e do amor nas coisas simples do dia a dia. Proclamada "
            "Doutora da Igreja em 1997 e padroeira das missões. Memória em 1º de outubro."
        ),
    },
    {
        "nome": "Santo Agostinho",
        "foto_url": "/static/santos/agostinho.jpg",
        "biografia": (
            "Bispo de Hipona (354–430) e Doutor da Igreja. Sua conversão é narrada nas "
            "Confissões, e sua obra A Cidade de Deus marcou o pensamento ocidental. "
            "Memória em 28 de agosto."
        ),
    },
    {
        "nome": "São Josemaria Escrivá",
        "foto_url": "/static/santos/josemaria.jpg",
        "biografia": (
            "Sacerdote espanhol (1902–1975) que fundou o Opus Dei em 1928, difundindo o "
            "chamado universal à santidade no trabalho e na vida cotidiana. Canonizado em "
            "2002. Memória em 26 de junho."
        ),
    },
    {
        "nome": "Santa Teresa d'Ávila",
        "foto_url": "/static/santos/teresa-de-avila.jpg",
        "biografia": (
            "Carmelita espanhola (1515–1582), reformadora do Carmelo e mestra da vida de "
            "oração, proclamada Doutora da Igreja. Autora de O Castelo Interior (As Moradas). "
            "Memória em 15 de outubro."
        ),
    },
]

ORACOES_SANTOS = [
    {
        "santo": "Santa Teresa d'Ávila",
        "titulo": "Nada te perturbe",
        "texto": (
            "Nada te perturbe, nada te espante. Tudo passa, só Deus não muda. A paciência "
            "tudo alcança. Quem a Deus tem nada lhe falta. Só Deus basta."
        ),
    },
    {
        "santo": "Santo Agostinho",
        "titulo": "Tarde te amei",
        "texto": (
            "Tarde te amei, ó Beleza tão antiga e tão nova, tarde te amei! Eis que estavas "
            "dentro de mim e eu fora, e fora te procurava."
        ),
    },
]

LIVROS = [
    {
        "titulo": "As Moradas (O Castelo Interior)",
        "autor": "Santa Teresa d'Ávila",
        "santo": "Santa Teresa d'Ávila",
        "resumo": "Descreve a vida de oração como a travessia de sete moradas no castelo interior da alma.",
        "contexto_historico": "Escrito em 1577, a pedido de superiores, já na maturidade espiritual da autora.",
    },
    {
        "titulo": "Confissões",
        "autor": "Santo Agostinho",
        "santo": "Santo Agostinho",
        "resumo": "Narrativa da juventude, da busca da verdade e da conversão de Agostinho, dirigida a Deus em forma de oração.",
        "contexto_historico": "Redigido por volta do ano 400, quando o autor já era bispo de Hipona.",
    },
    {
        "titulo": "Suma Teológica",
        "autor": "São Tomás de Aquino",
        "santo": "São Tomás de Aquino",
        "resumo": "Exposição sistemática da doutrina cristã em questões e artigos, em três partes.",
        "contexto_historico": "Obra da maturidade de Tomás, composta a partir de 1265 e deixada inacabada em 1273.",
    },
    {
        "titulo": "História de uma Alma",
        "autor": "Santa Teresinha do Menino Jesus",
        "santo": "Santa Teresinha do Menino Jesus",
        "resumo": "Manuscritos autobiográficos em que Teresinha expõe o seu 'pequeno caminho' de confiança.",
        "contexto_historico": "Publicado em 1898, após a morte da autora, e rapidamente difundido pelo mundo.",
    },
    {
        "titulo": "Caminho",
        "autor": "São Josemaria Escrivá",
        "santo": "São Josemaria Escrivá",
        "resumo": "Coletânea de pontos breves para a meditação, sobre oração, trabalho e vida cristã.",
        "contexto_historico": "Publicado em 1939, a partir de um texto anterior de 1934.",
    },
    {
        "titulo": "Teologia do Corpo",
        "autor": "São João Paulo II",
        "santo": None,
        "resumo": "Conjunto de catequeses de São João Paulo II sobre o amor humano no plano divino, proferidas nas audiências gerais de quarta-feira.",
        "contexto_historico": "As catequeses foram proferidas entre 5 de setembro de 1979 e 28 de novembro de 1984 e depois reunidas em edições com o título 'Teologia do Corpo: o amor humano no plano divino'.",
    },
    {
        "titulo": "O Cristão Bem Formado",
        "autor": "São João Bosco",
        "santo": None,
        "resumo": "Pequena obra que propõe uma norma de vida simples e prática para viver a fé com alegria, em oposição à ideia de que servir a Deus exige uma vida melancólica.",
        "contexto_historico": "Escrita por Dom Bosco (1815–1888), sacerdote italiano fundador dos salesianos, com foco na formação cristã dos jovens.",
    },
    {
        "titulo": "Todos os Caminhos Levam a Roma",
        "autor": "Scott Hahn",
        "santo": None,
        "resumo": "Testemunho da conversão de um pastor protestante à fé católica.",
        "contexto_historico": "Relato autobiográfico do casal Scott e Kimberly Hahn, publicado originalmente nos Estados Unidos.",
    },
]

NOVENA_TERESINHA = {  # novena já existente: texto preservado
    "titulo": "Novena a Santa Teresinha",
    "santo": "Santa Teresinha do Menino Jesus",
    "descricao": "Nove dias de reflexão inspirados no 'pequeno caminho' de confiança e amor.",
    "oracoes": ["Pai Nosso", "Ave Maria"],  # orações base originais desta novena
    "dias": [
        "Dia 1 – Confiança. Teresinha aprendeu que Deus não pede grandes feitos, mas um coração que confia. Entregue hoje a Ele as suas preocupações.",
        "Dia 2 – Simplicidade. A santidade está nas pequenas coisas feitas com amor. Que gesto simples você pode oferecer hoje?",
        "Dia 3 – Humildade. Reconhecer a própria pequenez abre espaço para a graça. Peça um coração humilde.",
        "Dia 4 – Paciência. Cada contrariedade pode ser oferecida como ato de amor. Que dificuldade você pode acolher hoje com serenidade?",
        "Dia 5 – Caridade. Teresinha escolheu o amor como vocação. Procure hoje alguém a quem possa servir em silêncio.",
        "Dia 6 – Abandono. Descansar nas mãos do Pai é confiar mesmo sem entender. Entregue o que foge ao seu controle.",
        "Dia 7 – Oração. Para ela, rezar era um impulso do coração. Reze hoje com palavras suas, sem pressa.",
        "Dia 8 – Missão. Mesmo no claustro, Teresinha abraçou o mundo com sua oração. Reze por quem precisa de Deus.",
        "Dia 9 – Gratidão. Agradeça pelos caminhos percorridos e peça a graça de perseverar no amor.",
    ],
}



ORACOES_NOVENA_PADRAO = ["Pai Nosso", "Ave Maria", "Glória ao Pai"]

# As reflexões abaixo foram redigidas para o Fides; NÃO são citações dos santos nem
# orações oficiais. Orações tradicionais (Pai Nosso, Ave Maria, Glória, "Nada te
# perturbe", "Tarde te amei") vêm do catálogo geral.
NOVENA_TERESA = {
    "titulo": "Novena a Santa Teresa d'Ávila",
    "santo": "Santa Teresa d'Ávila",
    "descricao": "Nove dias de reflexão sobre a vida de oração, inspirados em temas da espiritualidade de Santa Teresa d'Ávila. Textos de reflexão do Fides.",
    "dias": [
        "Dia 1 – Oração como amizade. Para Teresa, rezar era estar com Deus como se está com um amigo que sabemos que nos ama. Reserve hoje alguns minutos de silêncio e fale com Ele com simplicidade.",
        "Dia 2 – Recomeçar. Teresa conheceu períodos de frieza e voltou a Deus. Nenhum atraso na vida de oração é definitivo: comece de novo hoje, sem se desculpar demais.",
        "Dia 3 – O castelo interior. Teresa descreveu a alma como um castelo com muitas moradas, onde Deus habita no centro. Entre em si mesmo e reconheça que a presença de Deus já está aí.",
        "Dia 4 – Perseverança. A oração se constrói dia após dia, mesmo quando não há consolação. Escolha um horário realista e seja fiel a ele nesta semana.",
        "Dia 5 – Humildade e verdade. Andar na verdade é reconhecer os próprios limites e os dons recebidos. Agradeça a Deus pelo que você é e entregue o que ainda precisa ser curado.",
        "Dia 6 – Coragem para reformar. Teresa reformou o Carmelo enfrentando incompreensões. Peça a graça de corrigir, com firmeza e caridade, aquilo que em sua vida esfriou o amor.",
        "Dia 7 – Não desanimar nas securas. Há dias em que rezar parece vazio. Ofereça essa aridez a Deus: permanecer fiel já é uma forma de amar.",
        "Dia 8 – Oração que serve. Teresa uniu contemplação e ação, Maria e Marta. Que gesto concreto de serviço nasce da sua oração de hoje?",
        "Dia 9 – Só Deus basta. Ao concluir a novena, entregue seus pedidos com confiança e peça serenidade diante do que passa. Reze a oração 'Nada te perturbe'.",
    ],
    "extras": {9: ["Nada te perturbe"]},
}

NOVENA_AGOSTINHO = {
    "titulo": "Novena a Santo Agostinho",
    "santo": "Santo Agostinho",
    "descricao": "Nove dias de reflexão sobre a busca de Deus e a conversão, inspirados em temas da vida e da obra de Santo Agostinho. Textos de reflexão do Fides.",
    "dias": [
        "Dia 1 – O coração inquieto. Agostinho procurou longe de Deus aquilo que só Deus pode dar. Nomeie hoje a inquietação que você carrega e apresente-a ao Senhor.",
        "Dia 2 – A oração que persevera. A conversão de Agostinho foi acompanhada pelas lágrimas e orações de sua mãe, Santa Mônica. Reze hoje por alguém que você deseja ver mais perto de Deus.",
        "Dia 3 – Beleza antiga e nova. Agostinho reconheceu tarde que Deus estava dentro dele enquanto o procurava fora. Perceba hoje onde a beleza de Deus já se mostra no seu cotidiano. Reze 'Tarde te amei'.",
        "Dia 4 – Voltar-se para dentro. A verdade não se encontra na dispersão. Dedique um momento de silêncio, sem telas, para escutar o que Deus diz na sua consciência.",
        "Dia 5 – Humildade. Agostinho aprendeu que o orgulho fecha o caminho para Deus. Peça a graça de reconhecer sua necessidade de Deus e dos outros.",
        "Dia 6 – Graça e liberdade. A conversão é obra da graça que respeita a liberdade. Qual passo de conversão Deus lhe pede agora? Peça força para dá-lo.",
        "Dia 7 – O amor como medida. Para Agostinho, a vida cristã se resume em amar. Examine hoje seus gestos: onde o amor pode ser mais concreto?",
        "Dia 8 – Comunidade e Igreja. Agostinho viveu em comunidade e serviu como bispo. Agradeça pelas pessoas que o aproximam de Deus e reze pela Igreja.",
        "Dia 9 – Descansar em Deus. Ao concluir a novena, entregue suas buscas ao Senhor e peça a graça da perseverança, até que o coração encontre repouso em Deus.",
    ],
    "extras": {3: ["Tarde te amei"], 9: ["Tarde te amei"]},
}

NOVENAS = [NOVENA_TERESINHA, NOVENA_TERESA, NOVENA_AGOSTINHO]

# Grafias antigas de nomes (versões anteriores dos seeds) -> nome atual.
NOMES_LEGADOS = {"Santa Teresa d'Ávila": ["Santa Teresa de Ávila"]}


# --------------------------------------------------------------------------- #
# Configuração do administrador
# --------------------------------------------------------------------------- #
def _env(nome: str):
    valor = os.getenv(nome)
    return valor if valor not in (None, "") else None


def resolver_credenciais_admin() -> tuple:
    """Resolve (login, senha, email) a partir do ambiente.

    Login:  FIDES_ADMIN_LOGIN  -> padrão "adm".
    Senha:  FIDES_ADMIN_SENHA  -> FIDES_ADMIN_PASSWORD (alias) -> padrão de dev.
    Se as duas variáveis de senha existirem e forem diferentes, vale
    FIDES_ADMIN_SENHA e um aviso é emitido (sem expor os valores).
    """
    login = (_env("FIDES_ADMIN_LOGIN") or LOGIN_PADRAO_DEV).strip()
    senha_principal, senha_alias = _env("FIDES_ADMIN_SENHA"), _env("FIDES_ADMIN_PASSWORD")
    if senha_principal is not None:
        senha = senha_principal
        if senha_alias is not None and senha_alias != senha_principal:
            warnings.warn(
                "FIDES_ADMIN_SENHA e FIDES_ADMIN_PASSWORD estão definidas com valores "
                "diferentes; FIDES_ADMIN_SENHA tem precedência.", stacklevel=2)
    elif senha_alias is not None:
        senha = senha_alias
    else:
        senha = SENHA_PADRAO_DEV
    return login, senha, _env("FIDES_ADMIN_EMAIL")


# --------------------------------------------------------------------------- #
# Funções de seed (idempotentes)
# --------------------------------------------------------------------------- #
def migrar_esquema_administrador(session) -> None:
    """Adiciona a coluna de login a bancos criados pela versão anterior.

    ``create_all`` não altera tabelas existentes; sem isto, um banco antigo
    (Administradores só com e-mail) quebraria. Em banco novo é um no-op.
    """
    insp = inspect(session.connection())
    if "Administradores" not in insp.get_table_names():
        return
    colunas = {c["name"] for c in insp.get_columns("Administradores")}
    if "login_administrador" not in colunas:
        session.execute(text('ALTER TABLE "Administradores" ADD COLUMN login_administrador VARCHAR'))
        session.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS uq_administradores_login '
                             'ON "Administradores" (login_administrador)'))


def seed_momentos(session) -> dict:
    existentes = {m.bloco: m for m in session.scalars(select(MomentoDia))}
    for bloco in BlocoMomento:
        if bloco not in existentes:
            existentes[bloco] = MomentoDia(bloco=bloco)
            session.add(existentes[bloco])
    session.flush()
    return existentes


def seed_administrador(session, redefinir_senha: bool = False) -> Administrador:
    """Cria o administrador inicial sem duplicar e sem trocar senha existente.

    * Já existe admin com o login resolvido -> mantém (senha só muda com
      ``redefinir_senha=True``).
    * Existe admin da versão anterior (sem login) -> recebe o login, mantendo
      a senha que já tinha.
    * Caso contrário, cria o administrador com o hash da senha resolvida.
    """
    login, senha, email = resolver_credenciais_admin()
    admin = session.scalar(select(Administrador).where(Administrador.login == login))
    if admin is None:
        admin = session.scalar(select(Administrador).where(Administrador.login.is_(None))
                               .order_by(Administrador.id))
        if admin is not None:  # reconciliação do administrador legado
            admin.login = login
            print(f"[info] Administrador da versão anterior atualizado com o login '{login}'; "
                  "a senha anterior foi mantida (use --redefinir-senha-admin para trocá-la).")
    if admin is None:
        admin = Administrador(nome="Administrador FIDES", login=login, email=email)
        admin.definir_senha(senha)
        session.add(admin)
        if "FIDES_ADMIN_SENHA" not in os.environ and "FIDES_ADMIN_PASSWORD" not in os.environ:
            print(f"[aviso] Administrador criado com a senha PADRÃO de desenvolvimento "
                  f"(login '{login}'). Defina FIDES_ADMIN_SENHA antes de qualquer implantação pública.")
    elif redefinir_senha:
        admin.definir_senha(senha)
    session.flush()
    return admin


def _oracao_geral(session, titulo: str):
    return session.scalar(select(Oracao).where(Oracao.titulo == titulo, Oracao.santo_id.is_(None)))


def seed_oracoes(session, momentos: dict) -> None:
    """Cria o catálogo geral e alinha a classificação básica/complementar."""
    for lista, basica in ((ORACOES_BASICAS, True), (ORACOES_COMPLEMENTARES, False)):
        for item in lista:
            oracao = _oracao_geral(session, item["titulo"])
            if oracao is None:
                oracao = Oracao(titulo=item["titulo"], texto=item["texto"], basica=basica)
                session.add(oracao)
            elif oracao.basica != basica:
                oracao.basica = basica  # atualização controlada (classificação)
            for bloco in item["momentos"]:  # só acrescenta; nunca remove
                if momentos[bloco] not in oracao.momentos:
                    oracao.momentos.append(momentos[bloco])
    session.flush()


def seed_santos(session) -> dict:
    santos = {}
    for item in SANTOS:
        nomes = [item["nome"]] + NOMES_LEGADOS.get(item["nome"], [])
        santo = session.scalar(select(Santo).where(Santo.nome.in_(nomes)))
        if santo is None:
            santo = Santo(**item)
            session.add(santo)
        elif santo.nome != item["nome"]:
            santo.nome = item["nome"]  # atualização controlada (grafia), mesmo registro
        santos[item["nome"]] = santo
    session.flush()

    for item in ORACOES_SANTOS:
        santo = santos[item["santo"]]
        existe = session.scalar(select(Oracao).where(Oracao.titulo == item["titulo"],
                                                     Oracao.santo_id == santo.id))
        if existe is None:
            session.add(Oracao(titulo=item["titulo"], texto=item["texto"], basica=False,
                               santo_id=santo.id))
    session.flush()
    return santos


def seed_livros(session, santos: dict) -> None:
    for item in LIVROS:
        existe = session.scalar(select(Livro).where(Livro.titulo == item["titulo"]))
        if existe is None:
            session.add(Livro(
                titulo=item["titulo"], autor=item["autor"], resumo=item["resumo"],
                contexto_historico=item["contexto_historico"],
                santo_id=santos[item["santo"]].id if item["santo"] else None,
            ))
        else:  # atualização controlada: acompanha a grafia do nome do santo
            for atual, legados in NOMES_LEGADOS.items():
                if existe.autor in legados:
                    existe.autor = atual
    session.flush()


def seed_novenas(session, santos: dict, admin: Administrador) -> None:
    """Cadastra as novenas via ``Novena.cadastrar`` (valida token e os 9 dias)."""
    token = admin.emitir_token()
    for item in NOVENAS:
        if session.scalar(select(Novena).where(Novena.titulo == item["titulo"])):
            continue  # nunca reescreve uma novena existente
        base = [_oracao_geral(session, t).id for t in item.get("oracoes", ORACOES_NOVENA_PADRAO)]
        dias = []
        for numero, texto in enumerate(item["dias"], start=1):
            ids = list(base)
            for titulo in item.get("extras", {}).get(numero, []):
                oracao = session.scalar(select(Oracao).where(
                    Oracao.titulo == titulo, Oracao.santo_id == santos[item["santo"]].id))
                ids.append(oracao.id)
            dias.append({"texto_reflexao": texto, "oracoes_base_ids": ids})
        Novena.cadastrar(session, {"titulo": item["titulo"], "descricao": item["descricao"],
                                   "santo_id": santos[item["santo"]].id, "dias": dias}, token)
    session.flush()


def executar_seeds(session, redefinir_senha_admin: bool = False) -> None:
    """Executa todos os seeds na sessão dada (sem commit)."""
    migrar_esquema_administrador(session)
    momentos = seed_momentos(session)
    admin = seed_administrador(session, redefinir_senha_admin)
    seed_oracoes(session, momentos)
    santos = seed_santos(session)
    seed_livros(session, santos)
    seed_novenas(session, santos, admin)
    # Liturgia não é semeada: depende da data atual (janela de ±7 dias, RNF07)
    # e deve ser carregada pela integração com a fonte externa (Canção Nova).


def popular_banco(session, redefinir_senha_admin: bool = False) -> None:
    """Seeds em uma única transação: tudo é gravado ou nada é (rollback)."""
    try:
        executar_seeds(session, redefinir_senha_admin)
        session.commit()
    except Exception:
        session.rollback()
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria o banco do FIDES e popula os seeds.")
    parser.add_argument("--reset", action="store_true",
                        help="DESTRUTIVO: apaga todas as tabelas e TODOS os dados antes de recriar")
    parser.add_argument("--redefinir-senha-admin", action="store_true",
                        help="regrava a senha do administrador com o valor configurado")
    args = parser.parse_args()

    if args.reset:
        print(f"[ATENÇÃO] --reset: apagando todas as tabelas e dados de {DATABASE_URL}")
        apagar_tabelas()
    criar_tabelas()
    with SessionLocal() as session:
        popular_banco(session, args.redefinir_senha_admin)
    print("Banco criado e populado com sucesso.")


if __name__ == "__main__":
    main()

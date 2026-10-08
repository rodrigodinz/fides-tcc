"""Seeds iniciais do FIDES.

Os seeds são idempotentes: rodar duas vezes não duplica registros.
O conteúdo religioso aqui é inicial/demonstrativo e deve ser revisado e
ampliado pelo painel administrativo (US18-US22).

Variáveis de ambiente opcionais:
    FIDES_ADMIN_EMAIL, FIDES_ADMIN_PASSWORD
"""
import argparse
import os

from sqlalchemy import select

from .connection import SessionLocal, apagar_tabelas, criar_tabelas
from .models import (
    Administrador,
    BlocoMomento,
    Livro,
    MomentoDia,
    Novena,
    DiaNovena,
    Oracao,
    Santo,
)

# --------------------------------------------------------------------------- #
# Conteúdo
# --------------------------------------------------------------------------- #
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
]

# Orações de momentos específicos (não "básicas")
ORACOES_MOMENTOS = [
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
    {
        "titulo": "Santo Anjo",
        "texto": (
            "Santo Anjo do Senhor, meu zeloso guardador, se a ti me confiou a piedade divina, "
            "sempre me rege, guarda, governa e ilumina. Amém."
        ),
        "momentos": [BlocoMomento.ANTES_DE_DORMIR],
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
        "nome": "Santa Teresa de Ávila",
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
        "santo": "Santa Teresa de Ávila",
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
        "autor": "Santa Teresa de Ávila",
        "santo": "Santa Teresa de Ávila",
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
        "titulo": "Todos os Caminhos Levam a Roma",
        "autor": "Scott Hahn",
        "santo": None,
        "resumo": "Testemunho da conversão de um pastor protestante à fé católica.",
        "contexto_historico": "Relato autobiográfico do casal Scott e Kimberly Hahn, publicado originalmente nos Estados Unidos.",
    },
]

NOVENA_DEMO = {
    "titulo": "Novena a Santa Teresinha",
    "santo": "Santa Teresinha do Menino Jesus",
    "descricao": "Nove dias de reflexão inspirados no 'pequeno caminho' de confiança e amor.",
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


# --------------------------------------------------------------------------- #
# Funções de seed (idempotentes)
# --------------------------------------------------------------------------- #
def seed_momentos(session) -> dict:
    existentes = {m.bloco: m for m in session.scalars(select(MomentoDia))}
    for bloco in BlocoMomento:
        if bloco not in existentes:
            existentes[bloco] = MomentoDia(bloco=bloco)
            session.add(existentes[bloco])
    session.flush()
    return existentes


def seed_administrador(session) -> Administrador:
    email = os.getenv("FIDES_ADMIN_EMAIL", "admin@fides.local")
    senha = os.getenv("FIDES_ADMIN_PASSWORD", "admin123")
    admin = session.scalar(select(Administrador).where(Administrador.email == email))
    if admin is None:
        admin = Administrador(nome="Administrador FIDES", email=email)
        admin.definir_senha(senha)
        session.add(admin)
        session.flush()
        if "FIDES_ADMIN_PASSWORD" not in os.environ:
            print(f"[aviso] Administrador de desenvolvimento criado: {email} / {senha} "
                  "(defina FIDES_ADMIN_PASSWORD em produção)")
    return admin


def seed_oracoes(session, momentos: dict) -> None:
    for item in ORACOES_BASICAS + ORACOES_MOMENTOS:
        oracao = session.scalar(select(Oracao).where(Oracao.titulo == item["titulo"],
                                                     Oracao.santo_id.is_(None)))
        if oracao is None:
            oracao = Oracao(titulo=item["titulo"], texto=item["texto"],
                            basica=item in ORACOES_BASICAS)
            session.add(oracao)
        oracao.momentos = [momentos[b] for b in item["momentos"]]
    session.flush()


def seed_santos(session) -> dict:
    santos = {}
    for item in SANTOS:
        santo = session.scalar(select(Santo).where(Santo.nome == item["nome"]))
        if santo is None:
            santo = Santo(**item)
            session.add(santo)
        santos[santo.nome] = santo
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
    session.flush()


def seed_novena(session, santos: dict) -> None:
    if session.scalar(select(Novena).where(Novena.titulo == NOVENA_DEMO["titulo"])):
        return
    pai_nosso = session.scalar(select(Oracao).where(Oracao.titulo == "Pai Nosso"))
    ave_maria = session.scalar(select(Oracao).where(Oracao.titulo == "Ave Maria"))
    novena = Novena(titulo=NOVENA_DEMO["titulo"], descricao=NOVENA_DEMO["descricao"],
                    santo_id=santos[NOVENA_DEMO["santo"]].id)
    for numero, texto in enumerate(NOVENA_DEMO["dias"], start=1):
        novena.dias.append(DiaNovena(numero_dia=numero, texto_reflexao=texto,
                                     oracoes=[pai_nosso, ave_maria]))
    session.add(novena)
    session.flush()


def executar_seeds(session) -> None:
    momentos = seed_momentos(session)
    seed_administrador(session)
    seed_oracoes(session, momentos)
    santos = seed_santos(session)
    seed_livros(session, santos)
    seed_novena(session, santos)
    # Liturgia não é semeada: depende da data atual (janela de ±7 dias, RNF07) e deve ser carregada pela integração com a Canção Nova


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria o banco do FIDES e popula os seeds.")
    parser.add_argument("--reset", action="store_true", help="apaga todas as tabelas antes")
    args = parser.parse_args()

    if args.reset:
        apagar_tabelas()
    criar_tabelas()
    with SessionLocal() as session:
        executar_seeds(session)
        session.commit()
    print("Banco criado e populado com sucesso.")


if __name__ == "__main__":
    main()

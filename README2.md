# FIDES – Backend (banco de dados)

Camada de dados do FIDES: modelos SQLAlchemy a partir do Diagrama de Classes, banco SQLite e seeds.

## Estrutura
```
database/
  connection.py   engine (SQLite, FKs ativas), Base, SessionLocal, criar_tabelas()/apagar_tabelas()
  models.py       Santo, Oracao, MomentoDia, Novena, DiaNovena, Livro,
                  Liturgia (abstrata) > LiturgiaHora / LiturgiaDia, Administrador
  seeds.py        carga inicial idempotente
tests/test_models.py
```
O arquivo SQLite fica por padrão em `database.db`, na raiz do repositório (ignorado pelo git).
Para outro local: `FIDES_DATABASE_URL` (ex.: `sqlite:///C:/dados/fides.db`).

## Primeira execução
```bash
cd fides-backend                      # raiz do repositório (onde está requirements.txt)
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m database.seeds              # cria as tabelas (se faltarem) e popula
python -m pytest -q                   # testes (usam banco em memória; não tocam no database.db)
```
Para um banco que ainda não existe, o comando normal basta: ele cria o arquivo, as tabelas e os dados.

### Comandos dos seeds
| Comando | Efeito |
|---|---|
| `python -m database.seeds` | Cria tabelas que faltam e insere o que falta. Seguro para repetir. |
| `python -m database.seeds --redefinir-senha-admin` | Igual ao anterior e regrava a senha do administrador com o valor configurado. |
| `python -m database.seeds --reset` | **DESTRUTIVO:** apaga todas as tabelas e TODOS os dados e recria do zero. Nunca é usado automaticamente. |

### Política dos seeds
- Tudo roda em uma transação: se algo falhar, nada é gravado.
- Registros existentes **não** são duplicados nem recriados. Atualizações controladas (as únicas que alteram o que já existe):
  1. `Oracao.basica` é alinhada às listas do `seeds.py`;
  2. "Santa Teresa de Ávila" (grafia antiga) vira "Santa Teresa d'Ávila", no mesmo registro;
  3. administrador da versão anterior (sem login) recebe o login configurado e **mantém a senha antiga**.
- Associações oração ↔ momento do dia só são acrescentadas, nunca removidas.
- Bancos criados pela versão anterior ganham a coluna `login_administrador` automaticamente.

## Conteúdo inicial
5 santos · 8 livros · catálogo de orações (básicas: Pai Nosso, Ave Maria, Glória ao Pai, Credo, Santo Anjo; complementares: Invocação ao Espírito Santo, Oração a São Miguel Arcanjo, Oferecimento do dia, Bênção da refeição, Alma de Cristo; e 2 orações de santos) · 4 momentos do dia · 3 novenas (Santa Teresinha, Santa Teresa d'Ávila, Santo Agostinho; 9 dias cada).

As reflexões das novenas de Santa Teresa d'Ávila e Santo Agostinho foram redigidas para o Fides e não são citações dos santos. Revise o conteúdo religioso antes de publicar. As imagens (`foto_url`) são caminhos estáticos de exemplo; adicione os arquivos depois.

A **liturgia é dinâmica** (janela de ±7 dias, RNF07) e não é preenchida por seeds; deve vir da integração com a fonte externa.

## Administrador
| Variável | Efeito | Padrão (apenas desenvolvimento) |
|---|---|---|
| `FIDES_ADMIN_LOGIN` | login do administrador | `adm` |
| `FIDES_ADMIN_SENHA` | senha (nome principal) | `senha` |
| `FIDES_ADMIN_PASSWORD` | alias de compatibilidade; só vale se `FIDES_ADMIN_SENHA` não estiver definida | — |
| `FIDES_ADMIN_EMAIL` | e-mail opcional; também pode ser usado para entrar | nenhum |
| `FIDES_SECRET_KEY` | chave de assinatura dos tokens | valor de desenvolvimento |

Se as duas variáveis de senha existirem com valores diferentes, vale `FIDES_ADMIN_SENHA` e é emitido um aviso.
A senha só é gravada como hash (PBKDF2-HMAC-SHA256); a senha de um administrador existente não é alterada pelos seeds, salvo com `--redefinir-senha-admin`.

> **Atenção:** `adm` / `senha` é uma configuração temporária para desenvolvimento e demonstração do MVP.
> Defina `FIDES_ADMIN_SENHA` (senha forte) e `FIDES_SECRET_KEY` antes de qualquer implantação pública.

## Convenções
- Métodos de leitura recebem a `session`; `cadastrar`/`categorizar` exigem token de administrador (RNF05) e não dão `commit`.
- Listagens limitadas a 20 itens por página (RNF02); liturgia limitada a ±7 dias (RNF07).

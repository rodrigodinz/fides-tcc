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
| `python -m database.seeds --liturgia-referencia AAAA-MM-DD` | Igual ao primeiro, mas a janela de liturgia de demonstração (±7 dias) fica em torno da data informada (padrão: hoje). |
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
5 santos · 8 livros · catálogo de orações (básicas: Pai Nosso, Ave Maria, Glória ao Pai, Credo, Santo Anjo; complementares: Invocação do Espírito Santo, Oração a São Miguel Arcanjo, Oferecimento do dia, Bênção da refeição, Alma de Cristo; e 2 orações de santos) · 4 momentos do dia · 3 novenas (Santa Teresinha, Santa Teresa d'Ávila, Santo Agostinho; 9 dias cada).

As reflexões das novenas de Santa Teresa d'Ávila e Santo Agostinho foram redigidas para o Fides e não são citações dos santos. Revise o conteúdo religioso antes de publicar. As imagens (`foto_url`) são caminhos estáticos de exemplo; adicione os arquivos depois.

**Liturgia (MVP, RNF07):** os seeds criam, para cada dia da janela de ±7 dias em torno da data de referência, uma Liturgia do Dia (Primeira Leitura, Salmo, Evangelho; Segunda Leitura apenas aos domingos) e as três Liturgias das Horas (Laudes, Horas Médias, Vésperas). Os textos são **de demonstração** e identificados como tal; não reproduzem a liturgia oficial. Como a janela acompanha a data atual, execute os seeds novamente para renová-la (dias antigos não são apagados). Na Fase 2, o conteúdo virá de uma fonte externa confiável.

## Unicidade (aplicada pelo banco)
| Entidade | Regra |
|---|---|
| Santo | nome único |
| Livro | (título, autor) único |
| Novena | (santo, título) único |
| Oração | título único entre as orações gerais (sem santo); (santo, título) único entre as orações de santo |
| Liturgia do Dia | no máximo uma por data |

Os métodos `cadastrar` traduzem a violação em `RegistroDuplicadoError`; após esse erro a rota deve fazer `rollback`. A comparação é exata (diferença de maiúsculas/acentos conta como título diferente). Não há restrição de banco para repetir o mesmo bloco de `LiturgiaHora` na mesma data; os seeds evitam isso.

> **Atualizando um banco já existente:** o SQLite não adiciona restrições a tabelas prontas. Depois desta mudança, rode `python -m database.seeds --reset` **uma vez** para recriar o banco (apaga os dados; hoje eles vêm todos dos seeds).

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

## API REST (Back End)

API somente leitura (FastAPI) que serve ao React o conteúdo do banco. Documentação completa: [`docs/API.md`](docs/API.md).

### Executar (a partir da raiz do repositório)

```bash
pip install -r requirements.txt
python -m database.seeds                # cria e popula o banco (ver seção do banco de dados)
uvicorn api.main:app --reload           # http://127.0.0.1:8000  (docs interativas em /docs)
```

A API **não** cria tabelas, não roda seeds e não altera dados ao iniciar. Se o banco não existir, rode os seeds antes.

### Variáveis de ambiente da API

| Variável | Padrão | Descrição |
|---|---|---|
| `FIDES_CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Origens do Front End (separadas por vírgula) |
| `FIDES_STATIC_DIR` | `<raiz>/static` | Diretório servido em `/static` (imagens dos santos) |
| `FIDES_TIMEZONE` | `America/Sao_Paulo` | Fuso usado para "hoje" na liturgia (Linux/macOS) |

`FIDES_DATABASE_URL` e `FIDES_SECRET_KEY` continuam como descrito na seção do banco de dados.

### Testes

```bash
python -m pytest            # persistência (53) + API (204)
python -m pytest tests/api  # somente a API
```

Os testes usam bancos SQLite temporários e nunca tocam o `database.db`. O `pytest.ini` define `pythonpath = .`; se o repositório já tiver um `pytest.ini`/`conftest.py`, mantenha o seu e apenas garanta que a raiz esteja no `pythonpath`.

### Principais rotas (prefixo `/api/v1`)

`/santos`, `/santos/{id}`, `/oracoes`, `/momentos`, `/novenas`, `/novenas/{id}/dias/{n}`, `/livros`, `/livros/{id}`, `/liturgia/dia`, `/liturgia/horas`, além de `/health`. A liturgia é **de demonstração**.

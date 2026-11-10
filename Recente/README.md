# FIDES – Backend (banco de dados e API REST)

Camada de dados do FIDES (modelos SQLAlchemy a partir do Diagrama de Classes remodelado em 30/10/2026, banco SQLite e seeds) e a API REST que a expõe ao Front End.

## Estrutura
```
database/
  connection.py   engine (SQLite, FKs ativas), Base, SessionLocal, criar_tabelas()/apagar_tabelas()
  models.py       Santo, Oracao, Novena, Conteudo_Dia_Novena, Livro, Agenda, LiturgiaDia, LiturgiaHora
                  + MomentoDia (enum MomentoDoDia) e Administrador (autenticação)
  seeds.py        carga inicial idempotente
api/              API REST (FastAPI): main.py, config.py, errors.py, routes/, schemas/, services/
tests/test_models.py   testes do banco
tests/api/        testes da API (sem __init__.py)
docs/API.md       contrato da API
static/santos/    imagens dos santos (foto_url)
scripts/medir_desempenho.py
```
O arquivo SQLite fica por padrão em `database.db`, na raiz do repositório (ignorado pelo git).
Para outro local: `FIDES_DATABASE_URL` (ex.: `sqlite:///C:/dados/fides.db`).

> **Vindo da versão anterior do banco?** O esquema mudou (Agenda, liturgia sem herança, livro recomendado...). Um `database.db` antigo **não é atualizado automaticamente**: os seeds se recusam a rodar sobre ele e explicam o motivo. Siga `COMANDOS_ATUALIZACAO_BANCO.md`.

## Primeira execução
```bash
cd fides-tcc                          # raiz do repositório (onde está requirements.txt)
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m database.seeds              # cria as tabelas (se faltarem) e popula
python -m pytest tests/test_models.py -q   # testes do banco (usam banco em memória; não tocam no database.db)
```
Para um banco que ainda não existe, o comando normal basta: ele cria o arquivo, as tabelas e os dados.

### Comandos dos seeds
| Comando | Efeito |
|---|---|
| `python -m database.seeds` | Cria tabelas que faltam e insere o que falta. Seguro para repetir. Recusa bancos da versão anterior. |
| `python -m database.seeds --redefinir-senha-admin` | Igual ao anterior e regrava a senha do administrador com o valor configurado. |
| `python -m database.seeds --data-referencia AAAA-MM-DD` | Igual ao primeiro, usando a data informada (padrão: hoje) como centro da janela de liturgia e base das agendas das novenas. `--liturgia-referencia` continua aceito como sinônimo. |
| `python -m database.seeds --reset` | **DESTRUTIVO:** apaga TODAS as tabelas do arquivo (inclusive tabelas de versões antigas) e TODOS os dados, e recria do zero. Nunca é usado automaticamente. |

### Política dos seeds
- Tudo roda em uma transação: se algo falhar, nada é gravado.
- Os seeds **só criam o que falta**. Registros existentes não são duplicados, recriados nem alterados (classificação das orações, momentos do dia, agendas, textos e senha do administrador ficam como estão; a senha só muda com `--redefinir-senha-admin`).
- Banco criado por uma versão anterior dos models é recusado (`Erro_De_Esquema_Desatualizado`), porque `create_all` não altera tabelas existentes.

## Modelo de dados

| Classe (UML) | Tabela | Observações |
|---|---|---|
| Santo | `Santos` | `nome` único; `nome_busca` (sem acento) para a pesquisa. |
| Oração | `Oracoes` | `basica`; `santo_id` opcional; momentos do dia (N:N). |
| enum MomentoDoDia | `Momentos_Dia` + `Oracao_Momento_Dia` | 4 valores fixos: `AO_ACORDAR`, `REFEICOES`, `MISSA`, `ANTES_DE_DORMIR`. |
| Novena | `Novenas` | `santo_id` **opcional** (UML 0..1). |
| Conteudo_Dia_Novena | `Dias_Novena` + `Oracao_Dia_Novena` | Composição: exatamente 9 dias (1 a 9) por novena; orações base N:N. |
| Livro | `Livros` | `livro_recomendado` (US12/UC13); `santo_id` opcional. |
| Agenda | `Agendas` | `tipo` (NOVENA/LITURGIA), `data_inicio`, `data_fim`, `status` (ATIVA/CANCELADA/CONCLUIDA) e `id_novena` (opcional; só em agendas de novena). |
| LiturgiaDia | `Liturgia_Dia` | Pertence a uma agenda de liturgia (`id_agenda` obrigatório). Uma por data. |
| LiturgiaHora | `Liturgia_Hora` | Pertence a uma agenda de liturgia (`id_agenda` obrigatório). Um registro por (data, bloco). |
| — (ator Administrador) | `Administradores` | Login, hash de senha e token (não é classe da UML). |

**Regras principais**
- Excluir um santo **não** apaga suas orações, novenas e livros: eles ficam sem santo (`ON DELETE SET NULL`).
- Excluir uma novena apaga seus 9 dias; não é permitido enquanto houver agenda ativa (cancele antes).
- Agenda de novena: `data_fim = data_inicio + 8`; no máximo uma agenda ativa por novena; `calcular_dia_atual()` devolve 1–9 durante a novena e 0 fora dela (não começou, terminou ou foi cancelada).
- Liturgia de uma agenda cancelada deixa de aparecer nas consultas.
- Liturgia: consulta limitada a hoje ± 7 dias (RNF07, `Erro_Da_Liturgia_Fora_Da_Data_Permitida`).

## Conteúdo inicial
5 santos · 8 livros (2 recomendados: *O Castelo Interior* e *Caminho*) · catálogo de orações (básicas: Pai Nosso, Ave Maria, Glória ao Pai, Credo, Santo Anjo; complementares: Invocação do Espírito Santo, Oração a São Miguel Arcanjo, Oferecimento do dia, Bênção da refeição, Alma de Cristo; e 2 orações de santos) · 4 momentos do dia · 3 novenas (Santa Teresinha, Santa Teresa d'Ávila, Santo Agostinho; 9 dias cada) · 4 agendas · liturgia de demonstração (15 dias).

As reflexões das novenas de Santa Teresa d'Ávila e Santo Agostinho foram redigidas para o Fides e não são citações dos santos. Revise o conteúdo religioso antes de publicar. As imagens (`foto_url`) são caminhos estáticos de exemplo; adicione os arquivos depois.

**Agendas de demonstração (UC06, UC14):** na primeira execução, cada novena recebe uma agenda com início relativo à data de referência, para mostrar situações diferentes de "Dia X de 9": Teresinha em andamento (dia 5), Teresa d'Ávila começando (dia 1) e Agostinho ainda não iniciada (começa 2 dias depois). Os deslocamentos ficam em `Agenda_Novenas`, no `seeds.py`. Uma novena que já tem agenda não é reagendada pelos seeds.

**Liturgia (MVP, RNF07):** os seeds criam uma agenda de LITURGIA para a janela de ±7 dias em torno da data de referência e, para cada dia, uma Liturgia do Dia (Primeira Leitura, Salmo, Evangelho; Segunda Leitura apenas aos domingos) e as três Liturgias das Horas (Laudes, Horas Médias, Vésperas). Os textos são **de demonstração** e identificados como tal; não reproduzem a liturgia oficial. Como a janela acompanha a data atual, execute os seeds novamente para renová-la (dias antigos não são apagados). Na Fase 2, o conteúdo virá de uma fonte externa confiável.

## Unicidade (aplicada pelo banco)
| Entidade | Regra |
|---|---|
| Santo | nome único |
| Livro | (título, autor) único |
| Novena | título único entre as novenas sem santo; (santo, título) único entre as novenas de um santo |
| Oração | título único entre as orações gerais (sem santo); (santo, título) único entre as orações de santo |
| Agenda | no máximo uma agenda ATIVA por novena |
| Liturgia do Dia | no máximo uma por data |
| Liturgia das Horas | no máximo um registro por (data, bloco) |

Os métodos de escrita traduzem a violação em `Erro_De_Registros_Duplicados`; após esse erro a rota deve fazer `rollback`. A comparação é exata (diferença de maiúsculas/acentos conta como título diferente).

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
- Métodos de leitura recebem a `session` e são públicos (RNF06).
- Métodos de escrita (`cadastrar`, `atualizar`, `excluir`, `categorizar_por_momento_do_dia` e os da `Agenda`) exigem token de administrador (RNF05) e fazem `flush`, nunca `commit`. Eles existem no modelo, mas as **rotas de escrita são da Fase 2**; no MVP o conteúdo entra pelos seeds (RNF09).
- `atualizar(session, id, dados, token)` altera só os campos informados; `excluir(session, id, token)` não devolve nada.
- Exceções: `Erro_De_Autenticacao`, `Erro_De_Dados_Incorretos` e suas subclasses `Erro_De_Registros_Duplicados` e `Erro_De_Registro_Nao_Encontrado`, além de `Erro_Da_Liturgia_Fora_Da_Data_Permitida`.
- Listagens limitadas a 20 itens por página (RNF02); liturgia limitada a ±7 dias (RNF07).

## API REST (Back End)

API somente leitura (FastAPI), versão **0.2.0**, compatível com esta versão do banco (remodelagem de 30/10/2026). Ela serve ao React o conteúdo do banco. A documentação completa está em [`docs/API.md`](docs/API.md).

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
| `FIDES_TIMEZONE` | `America/Sao_Paulo` | Fuso usado para "hoje" na liturgia e na agenda (só Linux/macOS; no Windows vale o fuso do sistema) |

`FIDES_DATABASE_URL` e `FIDES_SECRET_KEY` continuam como descrito na seção do banco de dados.

### Rotas (todas GET e públicas; prefixo `/api/v1`, exceto `/health`)

| Rota | Conteúdo |
|---|---|
| `/santos`, `/santos/{id}` | Catálogo, busca sem acento (`?nome=`) e detalhe com orações, novenas e livros do santo |
| `/oracoes`, `/momentos` | Orações com filtros combináveis (`basica`, `momento_id`, `santo_id`) e momentos do dia |
| `/novenas`, `/novenas/{id}`, `/novenas/{id}/dias`, `/novenas/{id}/dias/{n}` | Catálogo, **progresso pela Agenda** ("Dia X de 9", situação e datas dos 9 dias) e conteúdo de cada dia |
| `/livros`, `/livros/{id}` | Catálogo e detalhe (resumo e contexto histórico) |
| `/livros/recomendados?santo_id=` | Recomendação de leitura: livros dos santos acessados pelo fiel (UC13) |
| `/liturgia/dia`, `/liturgia/horas` | Liturgia do Dia e Liturgia das Horas por data (hoje ± 7 dias) |
| `/agenda?data=` | Conteúdo agendado para a data: liturgia do dia, liturgia das horas e novenas em andamento |
| `/health` | Saúde da aplicação e do banco |

A liturgia é **de demonstração**. Pedidos de oração e marcações pessoais do fiel ficam no dispositivo; não há conta de fiel nem rotas de escrita (Fase 2). A coluna `Livro.livro_recomendado` não é usada pela API, porque a recomendação é feita pelos santos acessados.

### Preparar a janela de uma apresentação

Os seeds criam a liturgia para ±7 dias em torno de `--data-referencia` e agendam cada novena **uma única vez**. Por isso, para mudar as datas é preciso partir de um banco novo:

```powershell
Rename-Item database.db database_backup.db          # guarda o banco atual
python -m database.seeds --data-referencia 2026-11-25
```

Com a referência em 25/11, a liturgia cobre de 18/11 a 02/12. Na data de referência, a novena de Santa Teresinha está no dia 5, a de Santa Teresa d'Ávila no dia 1, e a de Santo Agostinho começa dois dias depois. Detalhes em `docs/API.md` (seção 9).

### Testes

```bash
python -m pytest            # persistência (tests/test_models.py) + API (263)
python -m pytest tests/api  # somente a API
```

Os testes usam bancos SQLite temporários e nunca tocam o `database.db`. O `pytest.ini` define `pythonpath = .`. A pasta `tests/api/` **não** deve ter `__init__.py`, porque isso conflita com o pacote `api`.

---

# Fides — Front-end (MVP web)

Aplicação React + Vite que consome a **API REST 0.2.0** do Fides (FastAPI) e aplica a identidade **Rococó Editorial**: *lógica na estrutura, beleza nos detalhes*.
Só faz requisições `GET`. Não há login, painel, CRUD nem agendamento: isso é da Fase 2.

## Requisitos

- Node.js 18 ou superior (testado com Node 22.23 e npm 10.9).
- A API do Fides rodando (ver o `README.md` da raiz do repositório).

## Primeira execução

```bash
# 1) API (na raiz do repositório, em outro terminal)
pip install -r requirements.txt
python -m database.seeds
uvicorn api.main:app --reload          # http://127.0.0.1:8000

# 2) Front-end
cd frontend
cp .env.example .env                   # opcional: ajuste VITE_API_URL
npm install
npm run dev                            # http://localhost:5173
```

O CORS padrão da API já libera `http://localhost:5173` e `http://localhost:3000`. Se abrir o front em outra origem (por exemplo `http://127.0.0.1:5173` ou o `npm run preview` em `:4173`), inclua-a em `FIDES_CORS_ORIGINS` ao iniciar a API.

## Scripts

| Comando | O que faz |
| --- | --- |
| `npm run dev` | Servidor de desenvolvimento (porta 5173) |
| `npm run build` | Build de produção em `dist/` |
| `npm run preview` | Serve o build (porta 4173), com fallback de SPA |
| `npm run lint` | ESLint (React, Hooks) |
| `npm test` | Testes (Vitest + Testing Library, ambiente jsdom) |

## Variáveis de ambiente

| Variável | Padrão | Uso |
| --- | --- | --- |
| `VITE_API_URL` | `http://127.0.0.1:8000` | Origem da API, sem barra final. Também é a base das imagens: `foto_url` (ex.: `/static/santos/teresinha.jpg`) é concatenado a ela. |

`.env.example` não contém segredos. O `.env` real fica fora do git.

## Hospedagem (fallback de SPA)

As rotas (`/santos/2`, `/novenas/1/dia/3`…) são do lado do cliente. No servidor estático, toda rota desconhecida deve devolver `index.html` (o `vite preview` já faz isso). Exemplos: Nginx `try_files $uri /index.html;`; Netlify `/* /index.html 200`.

## Estrutura

```
src/
  main.jsx, App.jsx        entrada, fontes, estilos e rotas
  navegacao.js             módulos do MVP (navbar e drawer)
  api/                     config.js (origem, urlImagem) · cliente.js (GET, erros, tempo limite)
                           servicos.js (um método por rota) · erros.js (mensagens amigáveis)
  hooks/                   useConsulta (carregando/sucesso/vazio/erro, cancela consultas antigas)
                           useDirecaoRolagem (navbar) · useDataNaUrl · useNovenaPessoal · useAtraso · useTitulo
  estado/                  armazenamento.js (localStorage seguro) · santosAcessados.js · novenaPessoal.js
  utils/                   datas, paginação, situação da agenda, ordem da Liturgia das Horas
  componentes/             layout (Navbar, Drawer, Rodape, Layout), Card, CardSanto, CardOracao, CardNovena,
                           RetratoSanto, Botao, Campos (busca, dropdown, chips), Paginacao, CalendarioNovena,
                           Estados (alerta, erro, vazio, carregando, não encontrado), Retorno (toast, modal),
                           Estrutura (cabeçalho, título de seção, migalhas), SeletorData, Liturgia, Ornamento, Icone
  paginas/                 Inicio, Santos, Santo, Oracoes, Novenas, Novena, Livros, Livro,
                           LiturgiaDia, LiturgiaHoras, Agenda, NaoEncontrada
  estilos/                 tokens.css (do Design System) · base.css · componentes.css · paginas.css
  assets/                  símbolo e ornamentos SVG (Famílias A e B)
  testes/                  setup e mock de fetch usado SÓ nos testes
docs/                      RELATORIO_FRONTEND.md e capturas/
```

## Rotas

| Rota | Página | API |
| --- | --- | --- |
| `/` | Início | `/agenda`, `/santos?limite=3`, `/livros/recomendados` (se houver santos acessados) |
| `/santos?nome=&pagina=` | Santos | `/santos` |
| `/santos/:id` | Santo | `/santos/{id}`, `/novenas?santo_id=`, `/oracoes?santo_id=` |
| `/oracoes?momento=&santo=&tipo=&pagina=` | Orações | `/momentos`, `/santos`, `/oracoes` |
| `/novenas?santo=&pagina=` | Novenas | `/novenas` |
| `/novenas/:id` e `/novenas/:id/dia/:n` | Novena e dia | `/novenas/{id}`, `/novenas/{id}/dias`, `/novenas/{id}/dias/{n}` |
| `/livros?santo=&pagina=` e `/livros/:id` | Livros | `/livros`, `/livros/{id}`, `/livros/recomendados` |
| `/liturgia?data=` | Liturgia do Dia | `/liturgia/dia` |
| `/liturgia/horas?data=` | Liturgia das Horas | `/liturgia/horas` |
| `/agenda?data=` | Agenda do dia | `/agenda` |

Filtros, página e data ficam na URL: recarregar ou compartilhar o endereço mantém a consulta.

## Dados guardados no dispositivo

Tudo em `localStorage`, com prefixo `fides:v1:`, nunca enviado à API:

- `santos-acessados`: até 20 ids, sem repetição, o mais recente primeiro (base da recomendação de livros).
- `novena:<id>`: `{marcados: [dias], pedidos: "texto", atualizadoEm}`.

Armazenamento indisponível, JSON inválido ou cota cheia não quebram a interface: os dados são ignorados ou o usuário é avisado.

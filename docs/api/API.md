# API REST do Fides (MVP) — Documentação técnica

API **somente leitura** (GET) que serve o conteúdo do banco SQLite ao Front End React. Cobre as histórias **US01–US17**. As histórias US18–US22 (painel administrativo) pertencem à Fase 2 e **não** têm rotas.

> **Aviso sobre a liturgia:** os textos de `/liturgia/*` são de **demonstração** (vêm dos seeds) e **não** são a liturgia oficial. Toda resposta litúrgica traz o campo `aviso`.

## 1. Arquitetura

```
React (navegador)  --HTTP/JSON-->  api/ (FastAPI)  --SQLAlchemy-->  database/ (models, SessionLocal)  -->  SQLite
```

| Camada       | Pasta                              | Responsabilidade |
|--------      |-------                             |------------------|
| Rotas        | `api/routes/`                      | Validar parâmetros, receber a sessão, chamar o serviço. Sem regra de negócio. |
| Schemas      | `api/schemas/`                     | Contrato público (Pydantic). Nenhum objeto ORM sai da API. |
| Serviços     | `api/services/`                    | Consultas (filtros, COUNT/LIMIT/OFFSET) e montagem das respostas. |
| Erros/config | `api/errors.py`, `api/config.py`   | Convenção de erros e variáveis de ambiente. |
| Persistência | `database/`                        | **Inalterada.** Sessão via `get_session()`; modelos e regras reaproveitados. |

Decisões: nenhuma segunda engine/fábrica de sessões; a API não cria tabelas, não roda seeds e não altera dados ao iniciar. Os serviços usam os métodos de leitura dos modelos (`Santo.buscar_id`, `Novena.buscar_id`, `DiaNovena.buscar_novena_dia`, `Livro.buscar_id`, `LiturgiaDia.buscar_data`, `LiturgiaHora.buscar_data`, `MomentoDia.listar_todos`). As **listagens** usam `select()` próprios porque os métodos do modelo não retornam o total exigido pela paginação.

## 2. Instalação e execução

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m database.seeds                             # cria/popula o banco (se ainda não existir)
uvicorn api.main:app --reload                        # a partir da raiz do repositório
```

- Base: `http://127.0.0.1:8000` · prefixo dos dados: `/api/v1` · saúde: `/health`
- Documentação interativa: `http://127.0.0.1:8000/docs` (OpenAPI em `/openapi.json`)

## 3. Variáveis de ambiente

| Variável | Padrão | Uso |
|---|---|---|
| `FIDES_DATABASE_URL` | `sqlite:///<raiz>/database.db` | Banco (já existente, lida por `database/`). |
| `FIDES_SECRET_KEY` | valor de desenvolvimento | Já existente; **não usada pela API no MVP** (não há login). |
| `FIDES_CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Origens do Front End, separadas por vírgula. |
| `FIDES_STATIC_DIR` | `<raiz>/static` | Diretório servido em `/static`. |
| `FIDES_TIMEZONE` | `America/Sao_Paulo` | Fuso para "hoje" (ver §8). |

## 4. Endpoints (todos `GET`, públicos)

| US | Endpoint | Parâmetros |
|---|---|---|
| — | `/health` | — |
| 01, 02 | `/api/v1/santos` | `pagina`, `limite`, `q` |
| 03 | `/api/v1/santos/{santo_id}` | — |
| 04, 05, 06 | `/api/v1/oracoes` | `pagina`, `limite`, `basica`, `momento_id`, `santo_id` |
| 06 | `/api/v1/momentos` | — |
| 07 | `/api/v1/novenas` | `pagina`, `limite`, `santo_id` |
| 08 | `/api/v1/novenas/{novena_id}`, `/api/v1/novenas/{novena_id}/dias` | — |
| 09, 10 | `/api/v1/novenas/{novena_id}/dias/{numero_dia}` | `numero_dia` 1–9 |
| 11, 12 | `/api/v1/livros` | `pagina`, `limite`, `santo_id` |
| 13 | `/api/v1/livros/{livro_id}` | — |
| 14, 17 | `/api/v1/liturgia/horas` | `data`, `bloco` (`laudes`, `horas_medias`, `vesperas`) |
| 15, 16, 17 | `/api/v1/liturgia/dia` | `data` |

Qualquer outro método (POST, PUT, PATCH, DELETE, HEAD) responde `405`. Parâmetros de query desconhecidos (ex.: `page`, `limit`) são **ignorados** pelo FastAPI: use exatamente `pagina` e `limite`.

## 5. Paginação e filtros

- `pagina` ≥ 1 (padrão 1, máximo 1.000.000) e `limite` de 1 a 20 (padrão 20; usa `LIMITE_MAXIMO_POR_PAGINA` de `database/models.py`). Valores fora disso → **422** (não são cortados em silêncio).
- COUNT, LIMIT e OFFSET são feitos no SQL; o `total` usa exatamente os mesmos filtros da listagem.
- Envelope: `{"itens": [...], "pagina": 1, "limite": 20, "total": 5, "total_paginas": 1}`.
- Página além do fim, filtro sem correspondência ou `santo_id`/`momento_id` inexistente → **200** com `itens: []`, `total: 0`, `total_paginas: 0`.
- Filtros de `/oracoes` são combináveis (E lógico). `momento_id` vem de `/momentos` (o React não deve fixar ids).
- `q` (santos): parcial, sem diferença de acento nem de caixa (`tomas` encontra "São Tomás de Aquino"); `%` e `_` são tratados como texto.
- Ordenação: santos por nome; orações, novenas e livros por título (desempate por id).

## 6. Contratos de resposta (exemplos reais, textos longos abreviados)

**`GET /api/v1/santos`** → envelope com itens `{"id", "nome", "foto_url"}`.

**`GET /api/v1/santos/5`**
```json
{"id": 5, "nome": "Santa Teresa d'Ávila", "foto_url": "/static/santos/teresa-de-avila.jpg",
 "biografia": "Carmelita espanhola ...",
 "oracoes": [{"id": 11, "titulo": "Nada te perturbe", "basica": false}],
 "novenas": [{"id": 2, "titulo": "Novena a Santa Teresa d'Ávila", "descricao": "Nove dias ..."}],
 "livros":  [{"id": 1, "titulo": "O Castelo Interior", "autor": "Santa Teresa de Jesus"}]}
```
O detalhe traz **resumos**; o texto completo das orações do santo vem de `/oracoes?santo_id=5`.

**`GET /api/v1/oracoes?basica=true&limite=2`** — item:
```json
{"id": 2, "titulo": "Ave Maria", "texto": "Ave Maria, cheia de graça ...", "basica": true, "santo": null,
 "momentos": [{"id": 1, "codigo": "ao_acordar", "nome": "Ao acordar"}, {"id": 4, "codigo": "antes_de_dormir", "nome": "Antes de dormir"}]}
```
`santo` é `{"id", "nome"}` ou `null` (orações gerais).

**`GET /api/v1/momentos`** → `[{"id": 1, "codigo": "ao_acordar", "nome": "Ao acordar"}, ...]` (ao_acordar, refeicoes, missa, antes_de_dormir).

**`GET /api/v1/novenas`** → itens `{"id", "titulo", "descricao", "santo": {"id","nome"}, "total_dias": 9}`. `/novenas/{id}` devolve o mesmo objeto.

**`GET /api/v1/novenas/1/dias`** → `{"novena": {"id","titulo"}, "total_dias": 9, "dias": [{"id", "numero_dia"}, ...]}` (ordenados, sem paginação).

**`GET /api/v1/novenas/1/dias/1`**
```json
{"novena": {"id": 1, "titulo": "Novena a Santa Teresinha"}, "numero_dia": 1, "total_dias": 9,
 "texto_reflexao": "Dia 1 – Confiança. ...",
 "oracoes": [{"id": 1, "titulo": "Pai Nosso", "texto": "..."}, {"id": 2, "titulo": "Ave Maria", "texto": "..."}],
 "dia_anterior": null, "proximo_dia": 2}
```
`dia_anterior` é `null` no dia 1 e `proximo_dia` é `null` no dia 9. As orações vêm ordenadas por id (ordem de cadastro).

**`GET /api/v1/livros`** → itens `{"id","titulo","autor","santo": {...}|null}`. **`/livros/{id}`** acrescenta `resumo` e `contexto_historico` (podem ser `null`).

**`GET /api/v1/liturgia/dia?data=AAAA-MM-DD`**
```json
{"data": "2026-10-14", "intervalo": {"hoje": "2026-10-14", "inicio": "2026-10-07", "fim": "2026-10-21"},
 "santo_celebrado": "...", "primeira_leitura": "...", "salmo": "...", "evangelho": "...",
 "segunda_leitura": null, "possui_segunda_leitura": false, "aviso": "Conteúdo de demonstração: ..."}
```
**`GET /api/v1/liturgia/horas`** → `{"data", "intervalo", "horas": [{"bloco": {"codigo": "laudes", "nome": "Laudes"}, "texto": "..."}], "avisos_integridade": [], "aviso": "..."}`. As horas saem na ordem canônica (Laudes, Horas médias, Vésperas), não na ordem de inserção. Sem `data`, vale hoje.

## 7. Erros

Formato único (inclusive 404 de rota, 405 e falhas de validação):
```json
{"erro": {"codigo": "PARAMETRO_INVALIDO", "mensagem": "Um ou mais parâmetros são inválidos.",
          "detalhes": [{"local": "query", "campo": "limite", "mensagem": "Deve ser menor ou igual a 20."}]}}
```

| HTTP | `codigo` | Quando |
|---|---|---|
| 400 | `DATA_FORA_DO_INTERVALO` | Data fora de hoje ± 7 dias (regra do modelo). |
| 404 | `RECURSO_NAO_ENCONTRADO` | Santo, novena, dia de novena ou livro inexistente. |
| 404 | `LITURGIA_NAO_CADASTRADA` | Data **dentro** da janela, mas sem registro. |
| 404 | `ROTA_NAO_ENCONTRADA` | Rota ou arquivo estático inexistente. |
| 405 | `METODO_NAO_PERMITIDO` | Método diferente de GET. |
| 422 | `PARAMETRO_INVALIDO` | Parâmetro malformado (data, número, enum, limite, dia fora de 1–9). |
| 500 | `ERRO_INTERNO` | Falha não prevista ou erro de consulta. Mensagem genérica; detalhes só no log. |
| 503 | `SERVICO_INDISPONIVEL` | Banco inacessível (arquivo não abre, bloqueado, erro de E/S). `/health` devolve 503 em qualquer falha de banco. |

Respostas de erro não trazem SQL, caminhos, rastreamento nem configuração. O 500 também envia cabeçalhos CORS, para o navegador conseguir ler a mensagem.

## 8. Regras da liturgia

- A janela (±7 dias) é a do modelo: `LiturgiaDia.buscar_data` / `LiturgiaHora.buscar_data` lançam `ForaDoIntervaloError` (→ 400). **A API não tem segunda regra de intervalo.** O campo `intervalo` usa a mesma constante (`INTERVALO_LITURGIA_DIAS`) e a mesma referência (`date.today()`).
- **Fuso horário:** o modelo usa `date.today()` do servidor. Ao criar a aplicação, a API ajusta o fuso do **processo** para `FIDES_TIMEZONE` (`time.tzset`), de modo que modelo e API enxerguem a mesma data. Isso só vale em Linux/macOS; no Windows vale o fuso do sistema. Os **seeds** (`python -m database.seeds`) usam o fuso da máquina onde rodam: para renovar a janela em hospedagem UTC, use `--liturgia-referencia AAAA-MM-DD`.
- Dia dentro da janela sem registro (ex.: seeds desatualizados) é diferente de data fora da janela: 404 `LITURGIA_NAO_CADASTRADA` × 400 `DATA_FORA_DO_INTERVALO`. A janela acompanha a data corrente: **reexecute os seeds periodicamente**.
- `segunda_leitura` só é preenchida quando cadastrada; não há geração de calendário nem de texto.
- **Bloco repetido:** o banco **permite** duas `LiturgiaHora` do mesmo bloco na mesma data. A API não falha: usa o registro de menor id, grava um *warning* no log e informa em `avisos_integridade`. O problema não é escondido; a correção é de dados.
- O `aviso` de demonstração está centralizado em `AVISO_DEMONSTRACAO` (`api/services/liturgia.py`); removê-lo/substituí-lo é a mudança prevista para a Fase 2.

## 9. Novenas e progresso individual (US08)

O banco guarda **apenas o conteúdo fixo** das novenas; **não existe entidade de progresso**, de pedidos de oração nem de usuário fiel, e a API não cria nenhuma. Ela entrega `total_dias`, `numero_dia`, `dia_anterior` e `proximo_dia`; o **React** controla localmente o dia atual, os dias concluídos e os pedidos (por exemplo, em `localStorage`, por dispositivo).

**Pendência funcional:** o critério de aceite da US08 fala em exibir "Dia 3 de 9" e carregar o texto "do dia correto" ao acessar a novena ativa. Isso é atendido com estado local **por dispositivo/navegador**. Se o requisito exigir progresso entre dispositivos ou pedidos guardados no servidor, será preciso decidir (e aprovar) uma entidade nova. Além disso, o Relatório Técnico de elicitação menciona uma "entidade específica para o rastreamento de progresso" que **não existe** nos modelos; o texto do TCC e o código precisam ser alinhados.

## 10. Imagens dos santos

`foto_url` é um **caminho relativo** (ex.: `/static/santos/tomas-de-aquino.jpg`) gravado no banco; a API não monta URLs absolutas. Os arquivos **ainda não existem** (`static/santos/` só tem `.gitkeep`): hoje `/static/...` responde 404 no formato padrão e a API segue funcionando.

No React, componha com a origem da API configurável:
```js
const API_ORIGEM = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";   // CRA: process.env.REACT_APP_API_URL
const urlFoto = (s) => (s.foto_url ? `${API_ORIGEM}${s.foto_url}` : null);       // use um avatar padrão se for null ou der erro no <img>
```
Para publicar as imagens, coloque os arquivos em `static/santos/` (ou aponte `FIDES_STATIC_DIR`).

## 11. CORS

`FIDES_CORS_ORIGINS` define as origens permitidas (padrão: `localhost:5173` e `localhost:3000`). Métodos permitidos: `GET` (e o preflight `OPTIONS`); sem credenciais. Origem não listada não recebe `Access-Control-Allow-Origin`; preflight com método de escrita é recusado (400). Em produção, liste apenas o domínio do Front End; evite `*`.

## 12. Testes

```bash
python -m pytest                    # tudo: 53 de persistência + 204 da API
python -m pytest tests/api          # só a API
python -m pytest tests/test_models.py
```
Os testes da API usam SQLite **temporário em arquivo** (`criar_engine` + `criar_tabelas` + `popular_banco`) e substituem `get_session`; nunca tocam `database.db`. O arquivo é usado em vez de `:memory:` porque o TestClient executa em outra thread. Para "data válida sem registro" semeia-se um banco com `--liturgia-referencia` deslocada; para "bloco repetido" insere-se a duplicata em um banco à parte. Nenhum teste depende de data fixa.

## 13. Desempenho (RNF01)

Medição feita em 14/10/2026, no ambiente de desenvolvimento da sessão, com `scripts/medir_desempenho.py`: servidor real (`uvicorn api.main:app`, sem `--reload`) sobre banco temporário criado pelos seeds, cliente `httpx` na mesma máquina, 200 requisições sequenciais por endpoint (após 1 de aquecimento). Ambiente: Python 3.12.3, Linux, 1 CPU, SQLite em arquivo, SQLAlchemy 2.1.4, FastAPI 0.143.0. Dados: 5 santos, 12 orações, 3 novenas (27 dias), 8 livros, 60 linhas de liturgia.

| Endpoint | p50 | p95 | máx. |
|---|---|---|---|
| `/health` | 1,67 ms | 3,05 ms | 3,63 ms |
| `/api/v1/santos` | 2,62 ms | 3,40 ms | 4,35 ms |
| `/api/v1/santos?q=tomas` | 2,62 ms | 3,32 ms | 8,12 ms |
| `/api/v1/santos/1` | 3,58 ms | 4,63 ms | 5,87 ms |
| `/api/v1/oracoes` | 3,59 ms | 4,69 ms | 47,26 ms |
| `/api/v1/oracoes?momento_id=1&basica=true` | 3,55 ms | 4,78 ms | 5,53 ms |
| `/api/v1/novenas/1/dias/1` | 3,20 ms | 4,14 ms | 9,18 ms |
| `/api/v1/liturgia/dia` | 2,23 ms | 2,94 ms | 4,93 ms |

**Leitura:** nestas condições, todas as consultas ficaram muito abaixo de 2 s. **Limitações:** volume minúsculo de dados; sem latência de rede real, sem concorrência e sem hospedagem; uma única máquina de 1 CPU; cache do SO aquecido. O resultado é **compatível** com o objetivo, mas o RNF01 só pode ser dado como atendido após medição no ambiente de hospedagem, com rede real e catálogo maior.

## 14. Limitações conhecidas

1. Progresso individual e pedidos de novena não são persistidos (§9).
2. Liturgia é demonstração; janela de ±7 dias exige reexecutar os seeds (§8). Sem integração externa.
3. **US05:** a história cita Pai Nosso, Ave Maria, Credo e **Invocação do Espírito Santo**, mas os seeds classificam a Invocação como *complementar* (`basica=false`) e incluem Glória ao Pai e Santo Anjo como básicas. `?basica=true` reflete os dados reais; **requisito e dados precisam ser alinhados** (decisão do responsável). A US05 não deve ser considerada integralmente validada.
4. Imagens dos santos ausentes (§10).
5. Sem rotas administrativas, login ou escrita (US18–US22, Fase 2).
6. Textos religiosos e reflexões dos seeds ainda aguardam revisão (pendência herdada do relatório do banco).
7. Numeração dos RNFs: esta documentação usa a dos documentos oficiais (RNF09 = REST, RNF10 = tolerância a falhas). O relatório do banco e os comentários de `seeds.py` citam "RNF09" para o povoamento por seeds, o que diverge da lista oficial; convém corrigir no texto do TCC.
8. `HEAD` não é suportado (405). Parâmetros desconhecidos são ignorados.
9. A API foi validada localmente; **não** está pronta para produção (hospedagem, HTTPS, CORS de produção, credenciais e imagens ainda pendentes).

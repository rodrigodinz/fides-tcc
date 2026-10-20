# Relatório 2 — Estado técnico atual do código (API REST)

*Versão de 14/10/2026.*

## Estrutura (arquivos novos; `database/` e `tests/test_models.py` inalterados)
```
api/main.py            create_app(), CORS, StaticFiles tolerante, routers; app = create_app()
api/config.py          Settings (FIDES_CORS_ORIGINS, FIDES_STATIC_DIR, FIDES_TIMEZONE), aplicar_fuso_horario()
api/errors.py          ApiError, handlers (validação, HTTP, SQLAlchemy, ForaDoIntervaloError), CapturaErrosInternos
api/routes/            health, santos, oracoes, novenas, livros, liturgia
api/schemas/           comum, santos, oracoes, novenas, livros, liturgia
api/services/          paginacao, busca, santos, oracoes, novenas, livros, liturgia
static/santos/.gitkeep
tests/api/             conftest.py, fides_helpers.py, test_infra/santos/oracoes/novenas/livros/liturgia/contrato.py
scripts/medir_desempenho.py
docs/                  API.md, README_secao_API.md, relatórios
pytest.ini             pythonpath = . ; testpaths = tests
requirements.txt       SQLAlchemy>=2.0, pytest>=8.0 (originais) + fastapi>=0.110, uvicorn[standard]>=0.29, httpx>=0.27
```
`tests/api/` **não** pode ter `__init__.py` (conflitaria com o pacote `api`).

## Execução
```
pip install -r requirements.txt
python -m database.seeds
uvicorn api.main:app --reload        # http://127.0.0.1:8000 ; /docs
python -m pytest                     # 257 testes
```
Versões usadas nesta sessão: Python 3.12.3, FastAPI 0.143.0, Starlette 1.8.0, Pydantic 2.14.1, SQLAlchemy 2.1.4, pytest 9.1.1, httpx 0.28.1, Uvicorn 0.54.0.

## Rotas (GET, públicas)
`/health` · `/api/v1/santos[?q,pagina,limite]` · `/api/v1/santos/{id}` · `/api/v1/oracoes[?basica,momento_id,santo_id,pagina,limite]` · `/api/v1/momentos` · `/api/v1/novenas[?santo_id,pagina,limite]` · `/api/v1/novenas/{id}` · `/api/v1/novenas/{id}/dias` · `/api/v1/novenas/{id}/dias/{1-9}` · `/api/v1/livros[?santo_id,pagina,limite]` · `/api/v1/livros/{id}` · `/api/v1/liturgia/horas[?data,bloco]` · `/api/v1/liturgia/dia[?data]` · `/static/...`

## Contratos principais
- Paginação: `{itens, pagina, limite, total, total_paginas}`; `limite` 1–20 (422 acima), `pagina` ≥ 1.
- Santo: lista `{id,nome,foto_url}`; detalhe + `biografia`, `oracoes[{id,titulo,basica}]`, `novenas[{id,titulo,descricao}]`, `livros[{id,titulo,autor}]`.
- Oração: `{id,titulo,texto,basica,santo|null,momentos[{id,codigo,nome}]}`.
- Novena: `{id,titulo,descricao,santo{id,nome},total_dias}`; dia: `{novena,numero_dia,total_dias,texto_reflexao,oracoes[{id,titulo,texto}],dia_anterior|null,proximo_dia|null}`.
- Livro: `{id,titulo,autor,santo|null}`; detalhe + `resumo`, `contexto_historico`.
- Liturgia: dia `{data,intervalo{hoje,inicio,fim},santo_celebrado,primeira_leitura,salmo,evangelho,segunda_leitura|null,possui_segunda_leitura,aviso}`; horas `{data,intervalo,horas[{bloco{codigo,nome},texto}],avisos_integridade[],aviso}`.
- Erro: `{"erro":{"codigo","mensagem","detalhes":[{local,campo,mensagem}]}}`. Códigos: `PARAMETRO_INVALIDO` 422, `RECURSO_NAO_ENCONTRADO` 404, `LITURGIA_NAO_CADASTRADA` 404, `DATA_FORA_DO_INTERVALO` 400, `ROTA_NAO_ENCONTRADA` 404, `METODO_NAO_PERMITIDO` 405, `ERRO_INTERNO` 500, `SERVICO_INDISPONIVEL` 503.
- Imagens: `foto_url` relativo; React concatena a origem da API (`docs/API.md` §10).

## Resultados dos testes (executados)
| Suíte | Resultado |
|---|---|
| `tests/test_models.py` (persistência) | 53 aprovados, 0 reprovados |
| `tests/api` | 204 aprovados, 0 reprovados |
| **Total** (`python -m pytest`) | **257 aprovados, 0 reprovados** (1 aviso de depreciação do Starlette/httpx) |

Cobertura funcional dos testes da API: saúde (200/503), 500 sem vazamento, CORS (origens, preflight), estáticos, fuso, somente leitura, paginação/limites, busca sem acento e caixa, relacionamentos de santos sem vazamento entre santos, filtros combinados de orações, novenas (dias 0 e 10, ids inexistentes), livros, liturgia (toda a janela, ±8 dias, datas malformadas, ordem canônica, Segunda Leitura só em domingo, data válida sem registro, bloco duplicado), ausência de termos sensíveis nas respostas.
**Não testado:** CORS/estáticos em hospedagem real; concorrência; fuso em Windows (sem `tzset`); medição de desempenho fora do ambiente da sessão.

## Desempenho (RNF01, ambiente da sessão)
p50 1,7–3,6 ms; p95 2,9–4,8 ms (200 req/endpoint, 1 CPU, 5 santos). Compatível com o objetivo de 2 s; **não** suficiente para declarar o RNF01 atendido em produção.

## Pendências e limitações
Ver Relatório 1 (US05, US08, liturgia de demonstração, imagens, numeração RNF, revisão de conteúdo, hospedagem). A API **não** está pronta para produção.

# Relatório 1 — Progresso recente (API REST do Fides)

*Data: 14/10/2026. Para colar nas conversas de Front End, Banco de Dados e Diretrizes Gerais.*

## O que foi feito
- API REST em **FastAPI** (somente GET, pública) sobre a persistência existente, cobrindo **US01–US17**: santos, orações, momentos, novenas, livros e liturgia, além de `/health`.
- Convenção única de erros, paginação no SQL (máx. 20), CORS configurável, `/static` configurável, documentação OpenAPI em `/docs`.
- Testes: **204 testes novos da API + 53 de persistência = 257 aprovados, 0 reprovados** (`python -m pytest`, Python 3.12.3, executado nesta sessão). O `test_models.py` e todo `database/` ficaram **sem nenhuma alteração** (conferido por `diff`). O `database.db` não foi criado nem tocado.
- Medição de desempenho (RNF01) com servidor real: p95 entre 2,9 e 4,8 ms em 8 endpoints (detalhes e limitações em `docs/API.md` §13).
- Documentação: `docs/API.md`, `docs/README_secao_API.md` (para anexar ao README), este relatório e o Relatório 2.

## Decisões tomadas
- Nenhum arquivo de `database/` foi alterado. Normalização de busca própria da API (`api/services/busca.py`), validada por teste contra o `nome_busca` gravado pelo modelo; o helper privado `_normalizar` **não** é importado.
- Janela de liturgia: **sem regra duplicada**. Os erros vêm de `ForaDoIntervaloError` do modelo. Para o fuso do Brasil, a API ajusta o fuso do processo (`FIDES_TIMEZONE`, `time.tzset`; só Linux/macOS), o que mantém API e modelo na mesma data de referência.
- `/health` na raiz (conforme o prompt de implementação), demais rotas em `/api/v1`.
- Filtros de orações: `basica`, `momento_id`, `santo_id`, combináveis. `GET /momentos` evita ids fixos no React.
- `/novenas/{id}/dias` devolve objeto `{novena, total_dias, dias}` (o planejamento previa só a lista) para facilitar o calendário.
- Bloco de `LiturgiaHora` repetido na mesma data: usa o menor id, registra *warning* e informa em `avisos_integridade`.
- Erros: 503 apenas para banco inacessível (arquivo não abre, bloqueado, E/S); falha de consulta (ex.: tabela ausente) é 500. Ambos testados com bancos reais, sem mock.
- Defeitos encontrados e corrigidos durante os testes: `/static` com diretório ausente dava 500 (agora 404); o erro 500 não carregava CORS (agora carrega).
- Numeração dos RNFs: oficial dos documentos do TCC.

## Pendências (precisam de decisão do responsável)
1. **US08:** não existe entidade de progresso; o progresso fica no estado local do React (por dispositivo). O critério de aceite ("dia correto") só é atendido nesse sentido. O relatório de elicitação cita uma "entidade de rastreamento de progresso" que não existe nos modelos: alinhar texto e código.
2. **US05:** a história inclui a Invocação do Espírito Santo, que nos seeds é *complementar*; os seeds marcam Glória ao Pai e Santo Anjo como básicas. Requisito e dados divergem; a US05 **não** está integralmente validada.
3. Liturgia é demonstração; a janela precisa de reexecução dos seeds. Seeds usam o fuso da máquina.
4. Imagens dos santos não existem (`/static/santos/*` dá 404).
5. Relatório do banco e `seeds.py` citam "RNF09" para o povoamento por seeds; na lista oficial RNF09 é REST. Corrigir no texto do TCC.
6. Conteúdo religioso dos seeds ainda não revisado (pendência herdada).
7. Resultado de desempenho vale só para o ambiente de teste; repetir na hospedagem.
8. Não foi possível ler o `README.md` do repositório; entreguei a seção a anexar (`docs/README_secao_API.md`). O `requirements.txt` real foi preservado, com FastAPI, Uvicorn e httpx acrescentados.
9. Aviso do Starlette 1.8 ao usar `httpx` no TestClient (sugere `httpx2`). Não afeta os resultados; não avaliei a migração.

## Próximos passos
Front End consumindo `/api/v1` (guia em `docs/API.md` §10 e §4); decidir US05/US08; adicionar imagens; hospedagem (variáveis, CORS, fuso, credenciais do administrador) e medição de RNF01 no ambiente final.

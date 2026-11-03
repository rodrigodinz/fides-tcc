# CONTEXTO DA ETAPA DE BACKEND — FIDES

*Documento de transferência de contexto (backend e API REST). Pode ser colado integralmente nas conversas de Diretrizes Gerais, Elicitação, POO, Banco de Dados, Frontend e Redes. Detalhes completos: `docs/RELATORIO_TECNICO_BACKEND_FIDES.md` (e `.tex`). Contratos por endpoint: `docs/API.md`.*

> **ALERTA — numeração dos RNFs.** Existem **duas listas** nos documentos do projeto. O Relatório Técnico de elicitação (`Relatorio_Tecnico_FIDES.pdf`) tem **RNF01–RNF11** (RNF09 = povoamento por seeds; RNF10 = REST; RNF11 = tolerância a falhas). O PDF de histórias de usuário e a Proposta têm **RNF01–RNF10** (RNF09 = REST; RNF10 = tolerância a falhas). Em relatórios anteriores do backend afirmou-se que citar RNF09 para os seeds era um erro: **isso só vale em relação à lista de 10 itens** e foi corrigido por errata. Este contexto usa a lista de **11 itens**, que coincide com o relatório do banco e com `database/seeds.py`. **Cabe ao responsável confirmar qual lista é a vigente e unificar.** Além disso, o RNF01 aparece como **2 s** (lista de 11 e Proposta) e como **3 s** (PDF de histórias).

## 1. Objetivo do Fides
Plataforma (web, depois mobile) que centraliza conteúdos e práticas devocionais católicas: santos, orações, novenas, textos importantes e liturgia. Projeto de TCC desenvolvido em etapas, com documentação acadêmica em LaTeX.

## 2. Escopo efetivamente implementado no backend
API REST **somente leitura (GET) e pública**, cobrindo US01–US17: santos (catálogo, busca, detalhe), orações (filtros combináveis), momentos do dia, novenas (catálogo, dias, dia com navegação), livros, liturgia das horas e do dia, `/health` e `/static`. **Não** há rotas de escrita, login, painel administrativo, persistência de progresso/pedidos nem integração externa de liturgia.

## 3. Arquitetura e tecnologias
Python, FastAPI, Uvicorn, SQLAlchemy 2.x, SQLite, Pydantic, pytest, httpx (exigido pelo `TestClient`). Camadas: rotas → schemas → serviços → `database/` (inalterado). A API reutiliza `get_session()` e os modelos; **sem** segunda engine/fábrica de sessões. A inicialização não cria tabelas, não roda seeds e não altera dados. `requirements.txt`: `SQLAlchemy>=2.0`, `pytest>=8.0`, `fastapi>=0.110`, `uvicorn[standard]>=0.29`, `httpx>=0.27`.

## 4. Estrutura relevante
```
api/        main.py config.py errors.py
            routes/ (health santos oracoes novenas livros liturgia)
            schemas/ (comum santos oracoes novenas livros liturgia)
            services/ (paginacao busca santos oracoes novenas livros liturgia)
database/   (inalterado) connection.py models.py seeds.py __init__.py
tests/      test_models.py (53, preexistente)   api/ (204; sem __init__.py!)
docs/       API.md  RELATORIO_1/2 (históricos, com errata)  README_secao_API.md
            CONTEXTO_BACKEND_FIDES.md  RELATORIO_TECNICO_BACKEND_FIDES.md/.tex
scripts/medir_desempenho.py   static/santos/   pytest.ini   requirements.txt
```
`tests/api/` **não pode** ter `__init__.py` (conflita com o pacote `api`).

## 5. Endpoints (todos GET; prefixo `/api/v1`, exceto `/health`)
`/health` · `/santos[?q,pagina,limite]` · `/santos/{id}` · `/oracoes[?basica,momento_id,santo_id,pagina,limite]` · `/momentos` · `/novenas[?santo_id,pagina,limite]` · `/novenas/{id}` · `/novenas/{id}/dias` · `/novenas/{id}/dias/{1-9}` · `/livros[?santo_id,pagina,limite]` · `/livros/{id}` · `/liturgia/horas[?data,bloco]` · `/liturgia/dia[?data]` · `/static/...`.
Paginação: `pagina` ≥ 1, `limite` 1–20 (acima de 20 → 422); envelope `{itens, pagina, limite, total, total_paginas}`; contagem e `LIMIT/OFFSET` no SQL. Erros: `{"erro": {"codigo", "mensagem", "detalhes"}}` com 400 `DATA_FORA_DO_INTERVALO`, 404 `RECURSO_NAO_ENCONTRADO` / `LITURGIA_NAO_CADASTRADA` / `ROTA_NAO_ENCONTRADA`, 405 `METODO_NAO_PERMITIDO`, 422 `PARAMETRO_INVALIDO`, 500 `ERRO_INTERNO`, 503 `SERVICO_INDISPONIVEL`. Respostas de liturgia trazem `aviso` (demonstração). Dia de novena traz `total_dias`, `dia_anterior`, `proximo_dia`.

## 6. Relação com o banco de dados
`database/` e `tests/test_models.py` permanecem **idênticos aos originais** (comparação byte a byte). A API usa os métodos de leitura dos modelos quando existem; para listagens com total, usa `select()` próprios sobre os mesmos modelos. Busca sem acento: `normalizar_busca` na API (o auxiliar do modelo é privado) + coluna `Santo.nome_busca`. Janela de liturgia: do modelo (`ForaDoIntervaloError` → 400); sem regra duplicada.

## 7. Decisões funcionais do responsável (não reabrir sem justificativa)
- **US08:** **sem** entidade de progresso, sem tabelas de progresso, sem login de fiéis. Progresso **local ao dispositivo** (estado do React). Não equivale a persistência individual nem a sincronização entre dispositivos; está fora do escopo.
- **Pedidos de oração (US09):** sem persistência no servidor.
- **US05:** a lista da história é **exemplificativa**; banco e seeds **mantidos** (orações básicas atuais: Pai Nosso, Ave Maria, Glória ao Pai, Credo, Santo Anjo).
- **Liturgia de demonstração** aceita no MVP (janela de 7 dias em torno da execução dos seeds; renovar rodando `python -m database.seeds`).
- **Imagens dos santos:** o responsável as adicionará (pendência de conteúdo, não defeito).
- **Conteúdo religioso dos seeds:** revisado pelo responsável (declaração dele; sem verificação teológica independente). Não é pendência.
- **Painel administrativo (US18–US22):** Fase 2. No MVP, apenas consulta pública.
- **Frontend:** primeiro definir a identidade visual (paleta, cores, ícone, tipografia, hierarquia de textos), depois as telas.

## 8. Resultado dos testes (ambiente Windows do responsável)
`python -m pytest` — Python 3.13.14, pytest 9.1.1, `.venv`: **257 coletados, 256 aprovados, 1 ignorado, 0 reprovados, 1 aviso.** O ignorado é `test_fuso_horario_e_aplicado_ao_processo` (`tests/api/test_infra.py`): `skipif` por falta de `time.tzset` no Windows (intencional, não é falha). O aviso é a depreciação do Starlette sobre httpx (sugere `httpx2`); sem efeito nos resultados; migração não avaliada. Em Linux (desenvolvimento) todos os 257 passam. Distribuição: 53 persistência + 204 API (infra 48, santos 41, liturgia 45, contrato 29, novenas 16, oracoes 14, livros 11). Servidor: `/health` e `/api/v1/santos?q=tomas` → 200; `/favicon.ico` → 404 (esperado).
**Desempenho (RNF01), ambiente de desenvolvimento:** p95 entre 2,94 e 4,78 ms em 8 endpoints (p50 1,67–3,59 ms; 200 requisições por endpoint; Linux, 1 CPU, Python 3.12.3; 5 santos). Compatível com o objetivo, **mas não comprova produção**: repetir na hospedagem.

## 9. Limitações conhecidas (aceitas no MVP salvo indicação)
Progresso/pedidos só locais; liturgia de demonstração com cobertura temporal curta (fora dela: 404 `LITURGIA_NAO_CADASTRADA`) e segunda leitura só aos domingos dos dados; imagens não confirmadas; sem rotas de escrita; parâmetros desconhecidos ignorados (`page`/`limit` não valem; usar `pagina`/`limite`); HEAD → 405; ajuste automático de fuso não funciona no Windows (usa o fuso do sistema); sem migrações estruturadas no banco.

## 10. Configurações e comandos
Variáveis: `FIDES_DATABASE_URL`, `FIDES_SECRET_KEY` (banco), `FIDES_CORS_ORIGINS` (padrão `http://localhost:5173,http://localhost:3000`), `FIDES_STATIC_DIR` (padrão `<raiz>/static`), `FIDES_TIMEZONE` (padrão `America/Sao_Paulo`).
```powershell
python -m venv .venv ; .venv\Scripts\activate
pip install -r requirements.txt
python -m database.seeds            # idempotente; NUNCA usar --reset (apaga tudo)
uvicorn api.main:app --reload       # http://127.0.0.1:8000  (docs em /docs)
python -m pytest                    # em outro terminal
```
Escuta apenas em `127.0.0.1` (não usar `--host 0.0.0.0` em rede corporativa). Imagens esperadas em `static/santos/`: `tomas-de-aquino.jpg`, `teresinha.jpg`, `agostinho.jpg`, `josemaria.jpg`, `teresa-de-avila.jpg` (minúsculas). URL no React: `API_ORIGEM + foto_url`.

## 11. Pendências reais
**Edição de documentos (decididas):** US05 (lista exemplificativa); US08 (progresso local ao dispositivo); remoção da menção à entidade de progresso no texto da Proposta. **Dependem de confirmação do responsável:** qual lista de RNFs vale e o valor do RNF01 (2 s × 3 s); redação de UC08/UC09 (registro local) e de US09 (pedidos locais); se o PDF do diagrama de classes é anterior à correção de 13/10/2026 (mostra `santo_id` como PK e `autenticar(email, senha)`); texto da Proposta que cita a Canção Nova como fonte de liturgia. **Conteúdo:** adicionar as 5 imagens (estado atual não confirmado). **Antes de publicar:** HTTPS; CORS restrito; trocar credenciais `adm`/senha de desenvolvimento e `FIDES_SECRET_KEY`; persistência do arquivo SQLite; fuso e renovação dos seeds de liturgia. **Antes de validar em hospedagem:** medir RNF01 lá. **Não são pendências:** revisão do conteúdo religioso; classificação das orações básicas.

## 12. Mudanças necessárias nas documentações antigas
| Artefato | Alteração | Situação |
|---|---|---|
| Proposta (texto sobre UML/POO) | Remover entidade de rastreamento de progresso; declarar acompanhamento local | Decidida; pendente de edição |
| US08 + critério de aceite | Explicitar "local ao dispositivo" | Decidida; pendente de edição |
| US05 | Lista como exemplos | Decidida; pendente de edição |
| US09 / UC08 / UC09 | Registro e pedidos locais (redação; diagrama estruturalmente válido) | Depende de confirmação |
| Diagrama de classes | Nada por causa do progresso; conferir versão (ver §11) | Depende de confirmação |
| Listas de RNFs / RNF01 | Unificar; confirmar valor | Depende de confirmação |
| Relatório do banco e comentário de `seeds.py` (RNF09) | Nenhuma se a lista de 11 for a vigente | Depende de confirmação |
| Proposta (liturgia/Canção Nova) | Fonte da Fase 2 em aberto | Depende de confirmação |
| `docs/API.md`, relatórios 1 e 2 do backend | Errata (RNF e data de medição não verificada) | **Já corrigida** |

## 13. Estado de conclusão
Backend **concluído para o escopo funcional do MVP** (consulta pública, US01–US17, com US05 e US08 conforme as decisões acima). **Não concluídos:** hospedagem, frontend, validação em produção, imagens, Fase 2.

## 14. Próxima etapa
Frontend (React): definir a identidade visual e só então as telas, consumindo a API por HTTP (nunca o SQLite). Conferir `docs/API.md` com o código antes de usá-lo como contrato.

## 15. Instruções por conversa
- **Frontend:** usar os contratos reais; `pagina`/`limite`; tratar 400/404/422/500/503 pelo `erro.codigo`; progresso da novena e pedidos em estado local (ex.: `localStorage`); foto = origem da API + `foto_url`; mostrar o `aviso` da liturgia.
- **Banco de dados:** preservar modelos, seeds e infraestrutura; qualquer mudança passa por essa conversa; não rodar `--reset` automaticamente.
- **POO/diagramas:** revisar só o que depende de progresso (UC08/UC09); não reconstruir diagramas válidos; conferir a versão do diagrama de classes.
- **Redes/hospedagem:** itens de "Antes de publicar"; nada está publicado; medir RNF01 lá; verificar fuso.
- **Diretrizes gerais/acadêmico:** usar o relatório técnico (e seu texto-base) e registrar a evolução incremental das decisões; unificar RNFs.
- **Elicitação:** editar US05, US08 e demais itens da seção 12.
- **Testes:** citar os resultados do Windows (256 + 1 ignorado); distinguir testes automatizados de validação em hospedagem.

## Contexto que deve ser preservado nas próximas conversas
1. API somente GET, pública, sem CRUD, sem login, sem painel (Fase 2).
2. **Sem** entidade de progresso: progresso e pedidos de novena são locais ao dispositivo.
3. `database/` e `tests/test_models.py` não foram alterados; a API reutiliza a persistência e **não** cria outra engine.
4. US05 é exemplificativa; classificação do banco mantida.
5. Liturgia é de demonstração; janela de ±7 dias do modelo; sem integração externa.
6. Conteúdo religioso revisado (declaração do responsável); imagens por adicionar.
7. Testes no Windows: 257 / 256 aprovados / 1 ignorado (`tzset`) / 0 reprovados.
8. RNF01: medição local favorável, **não** prova produção.
9. Numeração dos RNFs **dependente de confirmação** (11 × 10 itens); não afirmar que o RNF09 dos seeds está errado sem essa confirmação.
10. Backend concluído para o MVP ≠ hospedagem, frontend ou validação em produção concluídos.

---
### Registro de verificação deste documento
Inspecionados: código e testes de `api/` e `tests/api/` (repositório da sessão); `database/` e `test_models.py` (iguais aos originais); esquema OpenAPI (13 caminhos, todos GET); variáveis lidas por `getenv`; `História_de_Usuário_e_RNF.pdf`, `Relatorio_Tecnico_FIDES.pdf`, `Casos_de_Uso.pdf`, `Diagrama_de_Caso_de_Uso.pdf`, `Diagrama_de_Classes.pdf` e o texto da Proposta. **Não inspecionados/confirmados:** `README.md` do repositório do responsável; conteúdo real de `static/santos/` no repositório dele; `database.db` do responsável; versões do diagrama de classes posteriores ao PDF disponível. Resultados do Windows vêm do registro fornecido pelo responsável; os testes não foram reexecutados em Windows pela assistente.

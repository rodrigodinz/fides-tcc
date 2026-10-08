# FIDES – Backend (banco de dados)

Camada de dados do FIDES: modelos SQLAlchemy gerados a partir do Diagrama de Classes, banco SQLite e seeds.

## Estrutura
```
database/
  connection.py   engine (SQLite, FKs ativas), Base, SessionLocal, criar_tabelas()
  models.py       Santo, Oracao, MomentoDia, Novena, DiaNovena, Livro,
                  Liturgia (abstrata) > LiturgiaHora / LiturgiaDia, Administrador
  seeds.py        carga inicial idempotente
tests/test_models.py
```

## Como usar
```bash
pip install -r requirements.txt
python -m database.seeds            # cria database.db e popula
python -m database.seeds --reset    # apaga tudo e recria
python -m pytest -q
```

Variáveis de ambiente: `FIDES_DATABASE_URL`, `FIDES_SECRET_KEY` (assinatura do token),
`FIDES_ADMIN_EMAIL`, `FIDES_ADMIN_PASSWORD`.

## Relações
| Relação | Tipo |
|---|---|
| Santo → Oração / Novena / Livro | 1..* |
| Oração ↔ MomentoDia (`Oracao_Momento_Dia`) | N..N |
| Oração ↔ DiaNovena (`Oracao_Dia_Novena`) | N..N |
| Novena → DiaNovena | 1..9 (UNIQUE + CHECK 1–9) |
| Liturgia → LiturgiaHora / LiturgiaDia | herança por tabela unida |

## Convenções
- Métodos de leitura recebem a `session`; `cadastrar`/`categorizar` exigem token de administrador (RNF05) e não dão `commit`.
- Listagens limitadas a 20 itens por página (RNF02); liturgia limitada a ±7 dias (RNF07).

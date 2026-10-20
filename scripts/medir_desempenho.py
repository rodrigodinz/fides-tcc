"""Medição simples de latência (RNF01) contra uma API em execução.

Uso:  python scripts/medir_desempenho.py [URL_BASE] [N_REQUISICOES]
Ex.:  python scripts/medir_desempenho.py http://127.0.0.1:8000 200

Mede requisições GET sequenciais (uma por vez, cliente HTTP real) e imprime
p50, p95 e máximo em milissegundos. Não é um teste de carga.
"""
import statistics
import sys
import time

import httpx

ENDPOINTS = ["/health", "/api/v1/santos", "/api/v1/santos?q=tomas", "/api/v1/santos/1",
             "/api/v1/oracoes", "/api/v1/oracoes?momento_id=1&basica=true",
             "/api/v1/novenas/1/dias/1", "/api/v1/liturgia/dia"]


def percentil(valores, p):
    ordenados = sorted(valores)
    return ordenados[min(len(ordenados) - 1, int(round(p / 100 * (len(ordenados) - 1))))]


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    with httpx.Client(base_url=base, timeout=10) as cliente:
        for ep in ENDPOINTS:
            cliente.get(ep)  # aquecimento (descartado)
            tempos = []
            for _ in range(n):
                t0 = time.perf_counter()
                r = cliente.get(ep)
                tempos.append((time.perf_counter() - t0) * 1000)
                assert r.status_code == 200, (ep, r.status_code)
            print(f"{ep:45s} n={n} p50={statistics.median(tempos):6.2f}ms "
                  f"p95={percentil(tempos, 95):6.2f}ms max={max(tempos):6.2f}ms")


if __name__ == "__main__":
    main()

"""Uso:  python scripts/medir_desempenho.py [URL_BASE] [N_REQUISICOES]
Ex.:  python scripts/medir_desempenho.py http://127.0.0.1:8000 200
"""
import statistics
import sys
import time

import httpx

Rotas_Medidas = ["/health", "/api/v1/santos", "/api/v1/santos?nome=tomas", "/api/v1/santos/1",
                 "/api/v1/oracoes", "/api/v1/oracoes?momento_id=1&basica=true",
                 "/api/v1/novenas", "/api/v1/novenas/1/dias/1", "/api/v1/livros/recomendados?santo_id=1",
                 "/api/v1/liturgia/dia", "/api/v1/agenda"]


def calcular_percentil(valores, percentil):
    valores_ordenados = sorted(valores)
    posicao = min(len(valores_ordenados) - 1, int(round(percentil / 100 * (len(valores_ordenados) - 1))))
    return valores_ordenados[posicao]


def main():
    url_base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    quantidade_de_requisicoes = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    with httpx.Client(base_url=url_base, timeout=10) as cliente:
        for rota in Rotas_Medidas:
            cliente.get(rota)
            tempos_em_milissegundos = []
            for _ in range(quantidade_de_requisicoes):
                inicio = time.perf_counter()
                resposta = cliente.get(rota)
                tempos_em_milissegundos.append((time.perf_counter() - inicio) * 1000)
                assert resposta.status_code == 200, (rota, resposta.status_code)
            print(f"{rota:45s} n={quantidade_de_requisicoes} "
                  f"p50={statistics.median(tempos_em_milissegundos):6.2f}ms "
                  f"p95={calcular_percentil(tempos_em_milissegundos, 95):6.2f}ms "
                  f"max={max(tempos_em_milissegundos):6.2f}ms")


if __name__ == "__main__":
    main()

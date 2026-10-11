"""
Simulador de sensores do AgroSmart (fonte de dados da camada Bronze).

Gera o fluxo de leituras que um datalogger de campo enviaria pela Serial, no
formato CSV:  talhao_id,t_ms,umidade_solo_pct,temperatura_c,umidade_ar_pct,
luminosidade_pct,irrigacao. O cenario e uma sequencia de 2 min (60 leituras a
cada 2 s) em que o solo seca e o ar fica umido e quente: dispara os alertas de
irrigacao e de risco fungico do motor de regras.

Uso:  python simulacao/simulador_sensores.py                    # grava o CSV
      python simulacao/simulador_sensores.py --stdout --ritmo 1 # imprime linha a linha
"""
import os
import sys
import time
import random

CABECALHO = "talhao_id,t_ms,umidade_solo_pct,temperatura_c,umidade_ar_pct,luminosidade_pct,irrigacao"
N = 60
INTERVALO_MS = 2000
SAIDA = os.path.join("data", "bronze", "stream_sensores", "stream_simulado.csv")


def linhas(seed=7):
    rng = random.Random(seed)
    for i in range(N):
        p = i / (N - 1)
        solo = 62 - 44 * p + rng.uniform(-1.5, 1.5)          # seca ao longo da simulacao
        ar = 50 + 42 * p + rng.uniform(-2, 2)                # umidade do ar sobe
        temp = 22 + 8 * min(1, p * 1.4) + rng.uniform(-0.4, 0.4)
        luz = 55 + 35 * rng.uniform(-1, 1) * (1 - p) + rng.uniform(-3, 3)
        luz = max(0, min(100, luz))
        irrigar = 1 if solo < 30 else 0
        yield f"T1,{(i + 1) * INTERVALO_MS},{solo:.1f},{temp:.1f},{ar:.1f},{luz:.1f},{irrigar}"


if __name__ == "__main__":
    if "--stdout" in sys.argv:
        ritmo = float(sys.argv[sys.argv.index("--ritmo") + 1]) if "--ritmo" in sys.argv else 0
        print(CABECALHO, flush=True)
        for l in linhas():
            print(l, flush=True)
            time.sleep(ritmo)
    else:
        os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
        with open(SAIDA, "w", encoding="utf-8") as f:
            f.write(CABECALHO + "\n" + "\n".join(linhas()) + "\n")
        print(f"Gerado {SAIDA} ({N} leituras)")

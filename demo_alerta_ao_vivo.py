"""
Demo de automacao ao vivo: le a saida Serial (linha a linha, como chegaria do
datalogger) e dispara alerta + recomendacao no instante em que uma regra e violada.
Usa as MESMAS regras do motor (automacao._condicoes / REGRAS_SENSOR).
Cada alerta tambem e gravado em data/gold/alertas_ao_vivo.jsonl, que o
dashboard exibe com atualizacao automatica.

Uso:  python demo_alerta_ao_vivo.py                 # le o CSV emulado, 1 linha/s
      python demo_alerta_ao_vivo.py arquivo.csv 0.5 # outro arquivo, 0,5 s/linha
"""
import os
import sys
import csv
import json
import time
from datetime import datetime

from automacao import _condicoes, REGRAS_SENSOR

ENTRADA = os.path.join("data", "bronze", "stream_sensores", "stream_simulado.csv")
SAIDA = os.path.join("data", "gold", "alertas_ao_vivo.jsonl")


def main():
    arquivo = sys.argv[1] if len(sys.argv) > 1 else ENTRADA
    ritmo = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
    open(SAIDA, "w").close()
    ativos = set()
    ausente = {}   # leituras consecutivas sem a condicao (histerese contra oscilacao no limiar)
    print(f"[ao vivo] lendo {arquivo} ({ritmo}s por leitura). Ctrl+C para parar.\n")
    with open(arquivo, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            leitura = {k: float(row[k]) for k in
                       ("umidade_solo_pct", "temperatura_c", "umidade_ar_pct", "luminosidade_pct")}
            print(f"{row['talhao_id']} t={int(row['t_ms'])/1000:>5.0f}s  solo={leitura['umidade_solo_pct']:5.1f}%  "
                  f"temp={leitura['temperatura_c']:4.1f}C  ar={leitura['umidade_ar_pct']:5.1f}%  luz={leitura['luminosidade_pct']:5.1f}%")
            condicoes = _condicoes(leitura)
            for tipo, sev in condicoes.items():
                if tipo not in ativos:   # alerta so na transicao, nao a cada leitura
                    descricao, _, rec = REGRAS_SENSOR[tipo]
                    print(f"   >>> ALERTA [{sev.upper()}] {tipo}: {descricao}\n       Ação: {rec}", flush=True)
                    with open(SAIDA, "a", encoding="utf-8") as out:
                        out.write(json.dumps({
                            "hora": datetime.now().strftime("%H:%M:%S"), "talhao_id": row["talhao_id"],
                            "tipo": tipo, "severidade": sev, "descricao": descricao, "recomendacao": rec,
                            "t_ms": int(row["t_ms"]),
                        }, ensure_ascii=False) + "\n")
            for tipo in list(ativos):
                ausente[tipo] = 0 if tipo in condicoes else ausente.get(tipo, 0) + 1
            ativos = {t for t in ativos if ausente[t] < 3} | set(condicoes)
            time.sleep(ritmo)
    print("\n[ao vivo] fim do fluxo.")


if __name__ == "__main__":
    main()

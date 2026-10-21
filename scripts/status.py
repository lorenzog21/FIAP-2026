"""
Status do pipeline AgroSmart, lido de data/logs/execucoes.jsonl.

  python scripts/status.py                     # resumo legivel
  python scripts/status.py --json              # saida JSON
  python scripts/status.py --max-idade 900     # exit 1 se a ultima execucao tem >15 min ou falhou

Codigo de saida: 0 = operacional, 1 = atencao/falha, 2 = sem execucoes registradas.
E usado como HEALTHCHECK do servico `scheduler` no docker-compose.
"""
import os
import sys
import json
from datetime import datetime, timezone

EXECUCOES = os.path.join("data", "logs", "execucoes.jsonl")


def carregar(n=200):
    if not os.path.exists(EXECUCOES):
        return []
    with open(EXECUCOES, encoding="utf-8") as f:
        linhas = [json.loads(linha_) for linha_ in f if linha_.strip()]
    return linhas[-n:]


def avaliar(execs, max_idade=None):
    if not execs:
        return {"estado": "sem_dados", "codigo": 2}
    ult = execs[-1]
    fim = datetime.fromisoformat(ult["fim"])
    if fim.tzinfo is None:   # registros antigos, sem fuso, estavam em UTC
        fim = fim.replace(tzinfo=timezone.utc)
    idade = (datetime.now(timezone.utc) - fim).total_seconds()
    ok = sum(1 for e in execs if e["status"] == "sucesso")
    estado = "operacional"
    if ult["status"] != "sucesso":
        estado = "falha"
    elif max_idade is not None and idade > max_idade:
        estado = "desatualizado"
    return {
        "estado": estado, "codigo": 0 if estado == "operacional" else 1,
        "ultima_execucao": ult["run_id"], "status_ultima": ult["status"], "modo": ult.get("modo"),
        "idade_s": round(idade), "duracao_s": ult["duracao_s"], "execucoes_registradas": len(execs),
        "taxa_sucesso": round(ok / len(execs), 3), "alertas_sensor": ult.get("alertas_sensor"),
        "leituras_anomalas": ult.get("leituras_anomalas"), "leituras_sensor": ult.get("leituras_sensor"),
    }


if __name__ == "__main__":
    max_idade = int(sys.argv[sys.argv.index("--max-idade") + 1]) if "--max-idade" in sys.argv else None
    r = avaliar(carregar(), max_idade)
    if "--json" in sys.argv:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print("AgroSmart · status do pipeline")
        for k, v in r.items():
            print(f"  {k:<22} {v}")
    sys.exit(r["codigo"])

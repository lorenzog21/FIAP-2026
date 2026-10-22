"""Leitura dos event logs pela analise de processo."""
import csv
import json

import analise_processo as ap


def _escrever(pasta, run_ids, ts):
    logs = pasta / "data" / "logs"
    logs.mkdir(parents=True)
    with open(logs / "execucoes.jsonl", "w", encoding="utf-8") as f:
        for r in run_ids:
            f.write(json.dumps({"run_id": r, "status": "sucesso", "modo": "completo", "duracao_s": 1.0}) + "\n")
    with open(logs / "event_log_execucoes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "atividade", "inicio", "fim", "duracao_s", "recurso", "resultado", "registros", "observacao"])
        for r, t in zip(run_ids + ["em-andamento"], ts, strict=False):
            w.writerow([r, "ingestao", t, t, 0.1, "ingest.py", "ok", 1, ""])
    with open(logs / "event_log_folhas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["case_id", "run_id", "atividade", "inicio", "fim", "duracao_s", "recurso", "resultado", "talhao_id"])
        w.writerow([f"{run_ids[0]}:a.JPG", run_ids[0], "classificar_folha", ts[0], ts[0], 0.01, "x", "ok", "T1"])


def test_aceita_horarios_com_e_sem_fuso_e_ignora_execucao_nao_finalizada(pasta_tmp):
    _escrever(pasta_tmp, ["r1", "r2"], ["2026-10-21T18:00:00.123", "2026-10-21T18:00:05.123+00:00", "2026-10-21T18:00:09.000+00:00"])
    ex, fo, runs = ap.carregar()
    assert set(ex["case_id"]) == {"r1", "r2"}        # "em-andamento" nao tem resumo -> fora
    assert str(ex["inicio"].dt.tz) == "UTC" and len(fo) == 1 and list(runs["versao"]) == ["1.0", "1.0"]

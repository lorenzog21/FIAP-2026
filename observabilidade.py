"""
Observabilidade do pipeline AgroSmart (Fase 7).

Registra, a cada execucao do pipeline:
  - data/logs/app.log                    log estruturado (1 JSON por linha)
  - data/logs/execucoes.jsonl            resumo de cada execucao (status, duracao, contagens)
  - data/logs/event_log_execucoes.csv    event log por ETAPA  (caso = execucao do pipeline)
  - data/logs/event_log_folhas.csv       event log por FOLHA  (caso = folha analisada em uma execucao)

Os dois event logs seguem o formato usado em mineracao de processos:
case_id, atividade, inicio, fim, duracao_s, recurso, resultado (+ colunas extras).
Se nenhuma execucao estiver ativa, as funcoes viram no-ops, entao os modulos
continuam funcionando isolados (ex.: `python automacao.py`).
"""
import os
import csv
import json
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

LOG_DIR = os.path.join("data", "logs")
APP_LOG = os.path.join(LOG_DIR, "app.log")
EXECUCOES = os.path.join(LOG_DIR, "execucoes.jsonl")
EV_ETAPAS = os.path.join(LOG_DIR, "event_log_execucoes.csv")
EV_FOLHAS = os.path.join(LOG_DIR, "event_log_folhas.csv")

CAMPOS_ETAPAS = ["case_id", "atividade", "inicio", "fim", "duracao_s", "recurso", "resultado", "registros", "observacao"]
CAMPOS_FOLHAS = ["case_id", "run_id", "atividade", "inicio", "fim", "duracao_s", "recurso", "resultado", "talhao_id"]

VERSAO_PIPELINE = "1.1"  # 1.0 = antes da otimizacao da predicao (n_jobs=1 na inferencia)

atual = None  # execucao ativa


def _agora():
    """Horario em UTC com fuso explicito: containers e host nao misturam fusos no log."""
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat(timespec="microseconds")


def _append_csv(caminho, campos, linha):
    os.makedirs(LOG_DIR, exist_ok=True)
    novo = not os.path.exists(caminho) or os.path.getsize(caminho) == 0
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        if novo:
            w.writeheader()
        w.writerow({c: linha.get(c, "") for c in campos})


def log(nivel, mensagem, **campos):
    """Log estruturado em JSON (uma linha por evento)."""
    os.makedirs(LOG_DIR, exist_ok=True)
    registro = {"ts": _iso(_agora()), "nivel": nivel, "run_id": atual.run_id if atual else None,
                "msg": mensagem, **campos}
    with open(APP_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


class _Etapa:
    def __init__(self, execucao, atividade, recurso):
        self.execucao, self.atividade, self.recurso = execucao, atividade, recurso
        self.registros = None
        self.observacao = ""

    def __enter__(self):
        self.inicio = _agora()
        self._t0 = time.perf_counter()
        log("INFO", f"etapa iniciada: {self.atividade}", etapa=self.atividade)
        return self

    def __exit__(self, tipo, erro, tb):
        dur = time.perf_counter() - self._t0
        fim = _agora()
        resultado = "ok" if tipo is None else "erro"
        if erro is not None:
            self.observacao = f"{tipo.__name__}: {erro}"
        linha = {"case_id": self.execucao.run_id, "atividade": self.atividade, "inicio": _iso(self.inicio),
                 "fim": _iso(fim), "duracao_s": round(dur, 3), "recurso": self.recurso, "resultado": resultado,
                 "registros": self.registros if self.registros is not None else "", "observacao": self.observacao}
        _append_csv(EV_ETAPAS, CAMPOS_ETAPAS, linha)
        self.execucao.etapas.append({"atividade": self.atividade, "duracao_s": round(dur, 3),
                                     "resultado": resultado, "registros": self.registros})
        log("INFO" if tipo is None else "ERROR", f"etapa concluida: {self.atividade}", etapa=self.atividade,
            duracao_s=round(dur, 3), resultado=resultado, registros=self.registros)
        return False  # nao engole a excecao


class Execucao:
    def __init__(self, modo="completo", seed=0):
        global atual
        self.run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:4]
        self.modo, self.seed = modo, seed
        self.inicio = _agora()
        self._t0 = time.perf_counter()
        self.etapas = []
        self.resumo = {}
        atual = self
        log("INFO", "execucao iniciada", modo=modo, seed=seed)

    def etapa(self, atividade, recurso):
        return _Etapa(self, atividade, recurso)

    def finalizar(self, status="sucesso", **resumo):
        global atual
        dur = time.perf_counter() - self._t0
        registro = {"run_id": self.run_id, "inicio": _iso(self.inicio), "fim": _iso(_agora()),
                    "duracao_s": round(dur, 3), "status": status, "modo": self.modo, "seed": self.seed,
                    "versao": VERSAO_PIPELINE,
                    "etapas": self.etapas, **self.resumo, **resumo}
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(EXECUCOES, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        log("INFO" if status == "sucesso" else "ERROR", "execucao finalizada", status=status, duracao_s=round(dur, 3))
        atual = None
        return registro


@contextmanager
def folha(imagem, atividade, recurso, talhao_id=None):
    """Registra uma atividade de uma FOLHA no event log por folha. No-op sem execucao ativa.
    O bloco pode preencher `info['resultado']` (padrao 'ok')."""
    info = {"resultado": "ok", "talhao_id": talhao_id}
    if atual is None:
        yield info
        return
    inicio = _agora()
    t0 = time.perf_counter()
    try:
        yield info
    except Exception:
        info["resultado"] = "erro"
        raise
    finally:
        dur = time.perf_counter() - t0
        _append_csv(EV_FOLHAS, CAMPOS_FOLHAS, {
            "case_id": f"{atual.run_id}:{imagem}", "run_id": atual.run_id, "atividade": atividade,
            "inicio": _iso(inicio), "fim": _iso(_agora()), "duracao_s": round(dur, 6), "recurso": recurso,
            "resultado": info["resultado"], "talhao_id": info.get("talhao_id") or ""})

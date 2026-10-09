"""
Camada de ingestao (Bronze) do AgroSmart.

Gera/cataloga as fontes brutas do pipeline:
  - leituras simuladas de sensor de solo/clima, uma por talhao
  - metadados de imagem, ligando cada foto (treino e teste) a um talhao

Cada execucao grava um novo lote carimbado com data/hora em
data/bronze/ (append-only: nunca sobrescreve um lote anterior) e atualiza
o ponteiro data/bronze/LATEST_BATCH.txt para o lote mais recente.
"""
import os
import csv
import json
import random
import hashlib
from datetime import datetime, timedelta

TALHOES = ["T1", "T2", "T3", "T4"]
LEITURAS_POR_TALHAO = 40
INTERVALO_HORAS = 1
DATA_INICIAL = datetime(2026, 8, 1, 6, 0, 0)

FAIXAS_PLAUSIVEIS = {
    "umidade_solo_pct": (0, 100),
    "temperatura_c": (-10, 50),
    "umidade_ar_pct": (0, 100),
    "luminosidade_pct": (0, 100),
}

BRONZE_DIR = os.path.join("data", "bronze")
IMAGE_DIRS = {
    "Apple___healthy": os.path.join("data", "Apple___healthy"),
    "Apple___Black_rot": os.path.join("data", "Apple___Black_rot"),
}
TEST_DIR = "test"
EQUIPAMENTOS = ["drone", "camera_manual"]


def _hash_int(chave):
    return int(hashlib.md5(chave.encode("utf-8")).hexdigest(), 16)


# Cenario de simulacao por talhao: faixas (min, max) das bases de cada
# grandeza. Existem para exercitar todas as regras da automacao (Fase 6).
CENARIOS = {
    "T1": {"nome": "equilibrado",  "solo": (40, 60), "temp": (20, 26), "ar": (50, 70)},
    "T2": {"nome": "umido_quente", "solo": (68, 78), "temp": (26, 29), "ar": (78, 88)},
    "T3": {"nome": "seco",         "solo": (20, 28), "temp": (30, 33), "ar": (35, 50)},
    "T4": {"nome": "evento_chuva", "solo": (45, 55), "temp": (22, 27), "ar": (55, 65)},
}
# Janela (indices de leitura) em que o talhao T4 sofre um evento de chuva
EVENTO_CHUVA = range(14, 26)


def _gerar_leituras_talhao(talhao_id, rng):
    leituras = []
    cen = CENARIOS.get(talhao_id, CENARIOS["T1"])
    base_umidade_solo = rng.uniform(*cen["solo"])
    base_temp = rng.uniform(*cen["temp"])
    base_umidade_ar = rng.uniform(*cen["ar"])

    for i in range(LEITURAS_POR_TALHAO):
        ts = DATA_INICIAL + timedelta(hours=i * INTERVALO_HORAS)
        ciclo_diario = 6 * (0.5 - abs(((ts.hour - 15) % 24) / 24 - 0.5))

        umidade_solo = base_umidade_solo + rng.uniform(-8, 8)
        temperatura = base_temp + ciclo_diario + rng.uniform(-2, 2)
        umidade_ar = max(0, min(100, base_umidade_ar + rng.uniform(-10, 10)))
        if talhao_id == "T4" and i in EVENTO_CHUVA:
            umidade_ar = min(100, umidade_ar + 25)
            umidade_solo = min(100, umidade_solo + 28)
            temperatura -= 3
        # Luminosidade (LDR): curva de sol entre 6h e 18h, pico ao meio-dia
        sol = max(0.0, 1 - abs(ts.hour + ts.minute / 60 - 12) / 6)
        luminosidade = max(0.0, min(100.0, 95 * sol + rng.uniform(-5, 5)))

        # Falha de sensor simulada (~5% das leituras) para exercitar a validacao
        if rng.random() < 0.05:
            umidade_solo = rng.choice([-999.0, 150.0])

        leituras.append({
            "talhao_id": talhao_id,
            "timestamp": ts.isoformat(),
            "umidade_solo_pct": round(umidade_solo, 1),
            "temperatura_c": round(temperatura, 1),
            "umidade_ar_pct": round(umidade_ar, 1),
            "luminosidade_pct": round(luminosidade, 1),
        })
    return leituras


def _validar_leituras(leituras):
    n_flagged = 0
    for leitura in leituras:
        motivos = []
        for campo, (minimo, maximo) in FAIXAS_PLAUSIVEIS.items():
            valor = leitura[campo]
            if valor < minimo or valor > maximo:
                motivos.append(f"{campo}={valor} fora da faixa plausivel [{minimo}, {maximo}]")
        leitura["flag_anomalia"] = bool(motivos)
        leitura["motivo_flag"] = "; ".join(motivos) if motivos else None
        if motivos:
            n_flagged += 1
    return leituras, n_flagged


def _listar_imagens():
    imagens = []
    for label, path in IMAGE_DIRS.items():
        if not os.path.isdir(path):
            continue
        for f in sorted(os.listdir(path)):
            if f.upper().endswith(".JPG"):
                imagens.append((label, f))
    if os.path.isdir(TEST_DIR):
        for f in sorted(os.listdir(TEST_DIR)):
            if f.upper().endswith(".JPG"):
                imagens.append(("test", f))
    return imagens


def _gerar_metadados_imagens():
    linhas = []
    for classe_original, filename in _listar_imagens():
        h = _hash_int(filename)
        talhao_id = TALHOES[h % len(TALHOES)]
        equipamento = EQUIPAMENTOS[h % len(EQUIPAMENTOS)]
        offset_horas = h % (LEITURAS_POR_TALHAO * INTERVALO_HORAS)
        data_captura = DATA_INICIAL + timedelta(hours=offset_horas)
        linhas.append({
            "imagem_id": filename,
            "classe_original": classe_original,
            "talhao_id": talhao_id,
            "data_captura": data_captura.isoformat(),
            "equipamento": equipamento,
        })
    return linhas


def run_ingestion(seed=0):
    rng = random.Random(seed)
    batch_ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    sensor_dir = os.path.join(BRONZE_DIR, "sensores", f"batch_{batch_ts}")
    os.makedirs(sensor_dir, exist_ok=True)

    log = {"batch": batch_ts, "talhoes": {}}
    total_leituras = 0
    total_flagged = 0

    for talhao_id in TALHOES:
        leituras = _gerar_leituras_talhao(talhao_id, rng)
        leituras, n_flagged = _validar_leituras(leituras)
        out_path = os.path.join(sensor_dir, f"sensor_{talhao_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(leituras, f, indent=2, ensure_ascii=False)
        total_leituras += len(leituras)
        total_flagged += n_flagged
        log["talhoes"][talhao_id] = {"registros": len(leituras), "flagados": n_flagged}

    metadados = _gerar_metadados_imagens()
    metadados_path = os.path.join(BRONZE_DIR, f"metadados_imagens_{batch_ts}.csv")
    with open(metadados_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["imagem_id", "classe_original", "talhao_id", "data_captura", "equipamento"]
        )
        writer.writeheader()
        writer.writerows(metadados)

    esperado = len(_listar_imagens())
    log["imagens"] = {"catalogadas": len(metadados), "esperado": esperado}

    with open(os.path.join(BRONZE_DIR, "LATEST_BATCH.txt"), "w", encoding="utf-8") as f:
        f.write(batch_ts)

    with open(os.path.join(BRONZE_DIR, "ingestion_log.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")

    print(
        f"[ingest] lote {batch_ts}: {total_leituras} leituras de sensor "
        f"({total_flagged} flagadas para auditoria), {len(metadados)}/{esperado} imagens catalogadas."
    )

    return {"batch_ts": batch_ts, "sensor_dir": sensor_dir, "metadados_path": metadados_path}


def carregar_sensores(sensor_dir):
    sensores = {}
    for talhao_id in TALHOES:
        path = os.path.join(sensor_dir, f"sensor_{talhao_id}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                sensores[talhao_id] = json.load(f)
    return sensores


def carregar_metadados(metadados_path):
    metadados = {}
    with open(metadados_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            metadados[row["imagem_id"]] = row
    return metadados


def sensor_mais_proximo(leituras_talhao, data_captura_iso):
    if not leituras_talhao:
        return None
    alvo = datetime.fromisoformat(data_captura_iso)
    return min(leituras_talhao, key=lambda r: abs(datetime.fromisoformat(r["timestamp"]) - alvo))


if __name__ == "__main__":
    run_ingestion()

"""
Fase 6 - Processamento e preparacao dos dados.

Fluxo: Bronze (JSON de sensores + results.json) -> limpeza -> Silver
(sensores_limpos.csv) -> agregacoes -> Gold (dataset_dashboard.csv,
diagnosticos.csv).

- Leituras sinalizadas como anomalas (flag_anomalia) viram NaN e sao
  interpoladas no tempo dentro do talhao; a coluna `valor_imputado`
  preserva a rastreabilidade de quais linhas foram corrigidas.
- Cada leitura recebe `risco_ambiental` (0-1), calculado pela mesma
  funcao usada na IA generativa, para o dashboard e a automacao
  falarem a mesma lingua.
"""
import os
import json
import pandas as pd

from generate_insights import _risco_ambiental

SILVER_DIR = os.path.join("data", "silver")
GOLD_DIR = os.path.join("data", "gold")
CAMPOS_SENSOR = ["umidade_solo_pct", "temperatura_c", "umidade_ar_pct", "luminosidade_pct"]


def carregar_sensores_bronze(sensor_dir):
    frames = []
    for nome in sorted(os.listdir(sensor_dir)):
        if nome.startswith("sensor_") and nome.endswith(".json"):
            with open(os.path.join(sensor_dir, nome), encoding="utf-8") as f:
                frames.append(pd.DataFrame(json.load(f)))
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    if "luminosidade_pct" not in df:
        df["luminosidade_pct"] = float("nan")
    return df.sort_values(["talhao_id", "timestamp"]).reset_index(drop=True)


def limpar_sensores(df):
    df = df.copy()
    df["valor_imputado"] = df["flag_anomalia"].astype(bool)
    df.loc[df["flag_anomalia"].astype(bool), CAMPOS_SENSOR] = float("nan")
    # So preenche as lacunas, mantendo o que ja era valido
    for campo in CAMPOS_SENSOR:
        df[campo] = df.groupby("talhao_id")[campo].transform(
            lambda s: s.interpolate(limit_direction="both")
        )
    df["hora"] = df["timestamp"].dt.hour
    df["periodo_dia"] = pd.cut(
        df["hora"], bins=[-1, 5, 11, 17, 23], labels=["madrugada", "manha", "tarde", "noite"]
    ).astype(str)
    df["risco_ambiental"] = df.apply(
        lambda r: _risco_ambiental({c: r[c] for c in CAMPOS_SENSOR})[0], axis=1
    )
    return df


def resumo_por_talhao(df):
    return (
        df.groupby("talhao_id")
        .agg(
            leituras=("timestamp", "count"),
            leituras_corrigidas=("valor_imputado", "sum"),
            temperatura_media=("temperatura_c", "mean"),
            umidade_ar_media=("umidade_ar_pct", "mean"),
            umidade_solo_media=("umidade_solo_pct", "mean"),
            luminosidade_media=("luminosidade_pct", "mean"),
            risco_ambiental_medio=("risco_ambiental", "mean"),
            risco_ambiental_max=("risco_ambiental", "max"),
        )
        .round(2)
        .reset_index()
    )


def tabela_diagnosticos(results_path):
    with open(results_path, encoding="utf-8") as f:
        results = json.load(f)
    linhas = []
    for r in results:
        sensor = r.get("sensor_context") or {}
        meta = r.get("metadata") or {}
        linhas.append({
            "imagem": r["image"],
            "classe_prevista": r["predicted_class"],
            "prob_doente": r["probabilities_ml"].get("Apple___Black_rot"),
            "area_infectada_pct": r["analysis_infected_area"]["real_infected_area_percentage"],
            "talhao_id": meta.get("talhao_id") or sensor.get("talhao_id"),
            "data_captura": meta.get("data_captura"),
            "equipamento": meta.get("equipamento"),
            "umidade_ar_pct": sensor.get("umidade_ar_pct"),
            "temperatura_c": sensor.get("temperatura_c"),
            "umidade_solo_pct": sensor.get("umidade_solo_pct"),
            "luminosidade_pct": sensor.get("luminosidade_pct"),
        })
    return pd.DataFrame(linhas)


def processar(sensor_dir, results_path):
    os.makedirs(SILVER_DIR, exist_ok=True)
    os.makedirs(GOLD_DIR, exist_ok=True)

    bruto = carregar_sensores_bronze(sensor_dir)
    limpo = limpar_sensores(bruto)

    limpo.to_csv(os.path.join(SILVER_DIR, "sensores_limpos.csv"), index=False)
    limpo.drop(columns=["motivo_flag"]).to_csv(os.path.join(GOLD_DIR, "dataset_dashboard.csv"), index=False)
    resumo_por_talhao(limpo).to_csv(os.path.join(GOLD_DIR, "resumo_talhoes.csv"), index=False)
    diag = tabela_diagnosticos(results_path)
    diag.to_csv(os.path.join(GOLD_DIR, "diagnosticos.csv"), index=False)

    print(
        f"[processamento] {len(bruto)} leituras, {int(limpo['valor_imputado'].sum())} corrigidas; "
        f"{len(diag)} diagnosticos -> data/gold/dataset_dashboard.csv"
    )
    return limpo, diag


if __name__ == "__main__":
    with open(os.path.join("data", "bronze", "LATEST_BATCH.txt")) as f:
        lote = f.read().strip()
    processar(
        os.path.join("data", "bronze", "sensores", f"batch_{lote}"),
        os.path.join(GOLD_DIR, "results.json"),
    )

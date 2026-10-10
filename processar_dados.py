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


FAIXAS = {"umidade_solo_pct": (0, 100), "temperatura_c": (-10, 50),
          "umidade_ar_pct": (0, 100), "luminosidade_pct": (0, 100)}
SERIAL_DIR = os.path.join("data", "bronze", "stream_sensores")


def processar_serial():
    """Le o fluxo de sensores (CSV: talhao_id,t_ms,...,irrigacao), valida e
    grava data/silver/sensores_stream.csv. Trata: linhas de cabecalho repetidas,
    texto no lugar de numero (-> ausente), duplicatas de t_ms, fora de faixa e ausentes."""
    if not os.path.isdir(SERIAL_DIR):
        return None
    arquivos = sorted(f for f in os.listdir(SERIAL_DIR) if f.endswith(".csv"))
    if not arquivos:
        return None
    df = pd.concat([pd.read_csv(os.path.join(SERIAL_DIR, f)).assign(arquivo=f) for f in arquivos],
                   ignore_index=True)
    for c in ["t_ms", *FAIXAS, "irrigacao"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")        # "Temp: abc" ou celula vazia -> NaN
    df = df.dropna(subset=["t_ms"]).drop_duplicates(subset=["arquivo", "t_ms"]).sort_values(["arquivo", "t_ms"])
    df["valor_imputado"] = False
    for c, (lo, hi) in FAIXAS.items():
        invalido = df[c].isna() | (df[c] < lo) | (df[c] > hi)  # ausente ou outlier fisico
        df.loc[invalido, c] = float("nan")
        df["valor_imputado"] |= invalido
        df[c] = df.groupby("arquivo")[c].transform(lambda x: x.interpolate(limit_direction="both"))
    df["timestamp"] = DATA_BASE_SERIAL + pd.to_timedelta(df["t_ms"], unit="ms")
    df["irrigacao"] = (df["umidade_solo_pct"] < 30).astype(int)  # recalculada apos a limpeza
    df["risco_ambiental"] = df.apply(lambda r: _risco_ambiental({c: r[c] for c in FAIXAS})[0], axis=1)
    saida = df[["talhao_id", "timestamp", "t_ms", *FAIXAS, "irrigacao", "valor_imputado", "risco_ambiental", "arquivo"]]
    saida.to_csv(os.path.join(SILVER_DIR, "sensores_stream.csv"), index=False)
    return saida


DATA_BASE_SERIAL = pd.Timestamp("2026-08-01 06:00:00")


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

    serial = processar_serial()
    if serial is not None:
        print(f"[processamento] fluxo simulado: {len(serial)} leituras, "
              f"{int(serial['valor_imputado'].sum())} corrigidas -> data/silver/sensores_stream.csv")

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

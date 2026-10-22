"""Limpeza e preparacao dos dados de sensores."""
import pandas as pd

import processar_dados as pd_mod


def df_sensores(solo):
    n = len(solo)
    return pd.DataFrame({
        "talhao_id": ["T1"] * n,
        "timestamp": pd.date_range("2026-08-01 06:00", periods=n, freq="h"),
        "umidade_solo_pct": solo,
        "temperatura_c": [25.0] * n,
        "umidade_ar_pct": [60.0] * n,
        "luminosidade_pct": [50.0] * n,
        "flag_anomalia": [v < 0 or v > 100 for v in solo],
        "motivo_flag": [None] * n,
    })


def test_anomalia_e_interpolada_e_marcada():
    limpo = pd_mod.limpar_sensores(df_sensores([40.0, -999.0, 60.0]))
    assert limpo.loc[1, "umidade_solo_pct"] == 50.0
    assert limpo["valor_imputado"].tolist() == [False, True, False]


def test_colunas_derivadas():
    limpo = pd_mod.limpar_sensores(df_sensores([40.0, 41.0]))
    assert {"hora", "periodo_dia", "risco_ambiental"} <= set(limpo.columns)
    assert limpo["risco_ambiental"].between(0, 1).all()


def test_serial_trata_texto_vazio_duplicata_e_outlier(pasta_tmp, monkeypatch):
    serial = pasta_tmp / "serial"
    serial.mkdir()
    (pasta_tmp / "silver").mkdir()
    (serial / "log.csv").write_text(
        "talhao_id,t_ms,umidade_solo_pct,temperatura_c,umidade_ar_pct,luminosidade_pct,irrigacao\n"
        "T1,2000,50,25,60,40,0\n"
        "T1,4000,abc,26,61,41,0\n"
        "T1,6000,999,27,,42,0\n"
        "T1,6000,52,28,63,43,0\n"
        "T1,8000,53,29,64,44,0\n")
    monkeypatch.setattr(pd_mod, "SERIAL_DIR", str(serial))
    monkeypatch.setattr(pd_mod, "SILVER_DIR", str(pasta_tmp / "silver"))
    saida = pd_mod.processar_serial()
    assert len(saida) == 4                                    # duplicata de t_ms removida
    assert saida["valor_imputado"].tolist() == [False, True, True, False]
    assert saida["umidade_solo_pct"].between(0, 100).all()    # outlier 999 e texto corrigidos
    assert saida["umidade_ar_pct"].notna().all()              # celula vazia interpolada
    assert (pasta_tmp / "silver" / "sensores_stream.csv").exists()

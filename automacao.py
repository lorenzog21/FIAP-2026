"""
Fase 6 - Automacao inteligente baseada em dados (motor de regras).

Le o dataset processado (sensores + diagnosticos de imagem) e, sem
intervencao humana, produz:
  1. Alertas de sensor, consolidados em episodios (horas consecutivas
     com a mesma condicao viram um unico alerta com inicio, fim e pico).
  2. Classificacao de risco (baixo/medio/alto) de cada folha analisada,
     combinando a severidade da lesao e o risco ambiental do talhao.
  3. Uma recomendacao de acao por talhao.

Saidas em data/gold/: alertas.json, alertas.csv, risco_folhas.csv,
acoes_talhao.json.
"""
import os
import json
import pandas as pd

from generate_insights import _risco_ambiental, _recomendacao_por_severidade

GOLD_DIR = os.path.join("data", "gold")

# Regras de sensor: (tipo, descricao, severidade_base, recomendacao)
REGRAS_SENSOR = {
    "RISCO_FUNGICO": ("Condição favorável ao fungo (ar úmido + temperatura 24-32 °C)",
                      "media", "Intensificar monitoramento foliar e evitar irrigação por aspersão."),
    "SOLO_SECO": ("Umidade do solo abaixo de 30%",
                  "media", "Acionar irrigação no talhão."),
    "SOLO_ENCHARCADO": ("Umidade do solo acima de 80%",
                        "media", "Suspender irrigação e verificar drenagem."),
    "CALOR_EXTREMO": ("Temperatura acima de 35C",
                      "media", "Avaliar sombreamento ou irrigação de resfriamento."),
}


def _condicoes(linha):
    """Retorna {tipo: severidade} das regras ativadas por uma leitura."""
    ativas = {}
    if linha["umidade_ar_pct"] >= 75 and 24 <= linha["temperatura_c"] <= 32:
        ativas["RISCO_FUNGICO"] = "alta" if linha["umidade_ar_pct"] >= 85 else "media"
    if linha["umidade_solo_pct"] < 30:
        ativas["SOLO_SECO"] = "alta" if linha["umidade_solo_pct"] < 20 else "media"
    if linha["umidade_solo_pct"] > 80:
        ativas["SOLO_ENCHARCADO"] = "media"
    if linha["temperatura_c"] > 35:
        ativas["CALOR_EXTREMO"] = "media"
    return ativas


def alertas_de_sensor(df):
    """Consolida leituras consecutivas com a mesma condicao em episodios."""
    ordem = {"media": 1, "alta": 2}
    episodios = []
    for talhao, grupo in df.sort_values("timestamp").groupby("talhao_id"):
        abertos = {}
        for _, linha in grupo.iterrows():
            ativas = _condicoes(linha)
            for tipo, sev in ativas.items():
                ep = abertos.get(tipo)
                if ep is None:
                    abertos[tipo] = ep = {
                        "talhao_id": talhao, "tipo": tipo, "origem": "sensor",
                        "inicio": linha["timestamp"], "fim": linha["timestamp"],
                        "severidade": sev, "leituras": 0,
                    }
                    episodios.append(ep)
                ep["fim"] = linha["timestamp"]
                ep["leituras"] += 1
                if ordem[sev] > ordem[ep["severidade"]]:
                    ep["severidade"] = sev
            for tipo in [t for t in abertos if t not in ativas]:
                del abertos[tipo]

    saida = []
    for ep in episodios:
        descricao, _, recomendacao = REGRAS_SENSOR[ep["tipo"]]
        saida.append({
            **ep,
            "inicio": ep["inicio"].isoformat(),
            "fim": ep["fim"].isoformat(),
            "descricao": descricao,
            "recomendacao": recomendacao,
        })
    return saida


def classificar_folha(area_pct, classe, sensor):
    """Risco combinado (0-1) = 70% severidade da lesao + 30% risco ambiental.
    Mesma formula da IA generativa, para o texto e a classe nunca divergirem."""
    risco_amb, fatores = _risco_ambiental(sensor)
    if classe == "Apple___healthy":
        indice = round(risco_amb * 0.3, 2)
        nivel = "baixo"
        acao = ("Monitoramento preventivo: ambiente favorável ao fungo."
                if risco_amb >= 0.4 else "Manter inspeção periódica.")
        return indice, nivel, acao, fatores
    indice = round(min(1.0, (area_pct / 100) * 0.7 + risco_amb * 0.3), 2)
    nivel = "alto" if indice >= 0.6 else "medio" if indice >= 0.35 else "baixo"
    return indice, nivel, _recomendacao_por_severidade(area_pct), fatores


def risco_das_folhas(diag):
    linhas = []
    for _, r in diag.iterrows():
        sensor = {
            "umidade_ar_pct": r["umidade_ar_pct"], "temperatura_c": r["temperatura_c"],
            "umidade_solo_pct": r["umidade_solo_pct"],
        } if pd.notna(r["umidade_ar_pct"]) else None
        indice, nivel, acao, fatores = classificar_folha(
            r["area_infectada_pct"], r["classe_prevista"], sensor
        )
        linhas.append({
            "imagem": r["imagem"], "talhao_id": r["talhao_id"],
            "classe_prevista": r["classe_prevista"],
            "area_infectada_pct": r["area_infectada_pct"],
            "indice_risco": indice, "nivel_risco": nivel,
            "fatores_ambientais": "; ".join(fatores), "acao_recomendada": acao,
        })
    return pd.DataFrame(linhas)


def acoes_por_talhao(risco, alertas):
    ordem = {"baixo": 0, "medio": 1, "alto": 2}
    acoes = []
    for talhao in sorted(set(risco["talhao_id"].dropna())):
        folhas = risco[risco["talhao_id"] == talhao]
        doentes = folhas[folhas["classe_prevista"] == "Apple___Black_rot"]
        pior = max(folhas["nivel_risco"], key=ordem.get)
        n_alertas_altos = sum(1 for a in alertas if a["talhao_id"] == talhao and a["severidade"] == "alta")
        if pior == "alto" or n_alertas_altos:
            prioridade = "alta"
        elif pior == "medio" or len(doentes):
            prioridade = "media"
        else:
            prioridade = "baixa"
        meus_alertas = [a for a in alertas if a["talhao_id"] == talhao]
        passos = []
        if pior == "alto":
            passos.append("Inspeção em campo e tratamento fungicida conforme orientação agronômica.")
        elif len(doentes):
            passos.append("Remover as folhas afetadas e reavaliar em 48 h.")
        tipos = sorted({a["tipo"] for a in meus_alertas},
                       key=lambda t: -sum(1 for a in meus_alertas if a["tipo"] == t and a["severidade"] == "alta"))
        passos += [REGRAS_SENSOR[t][2] for t in tipos]
        acoes.append({
            "talhao_id": talhao,
            "folhas_analisadas": int(len(folhas)),
            "folhas_com_black_rot": int(len(doentes)),
            "pior_nivel_risco": pior,
            "alertas_sensor": len(meus_alertas),
            "causas": tipos,
            "prioridade": prioridade,
            "decisao": " ".join(passos) if passos else "Sem ação corretiva; manter rotina de inspeção.",
        })
    return acoes


def executar():
    sensores = pd.read_csv(os.path.join(GOLD_DIR, "dataset_dashboard.csv"), parse_dates=["timestamp"])
    diag = pd.read_csv(os.path.join(GOLD_DIR, "diagnosticos.csv"))

    alertas = alertas_de_sensor(sensores)
    risco = risco_das_folhas(diag)
    acoes = acoes_por_talhao(risco, alertas)

    with open(os.path.join(GOLD_DIR, "alertas.json"), "w", encoding="utf-8") as f:
        json.dump(alertas, f, indent=2, ensure_ascii=False)
    pd.DataFrame(alertas).to_csv(os.path.join(GOLD_DIR, "alertas.csv"), index=False)
    risco.to_csv(os.path.join(GOLD_DIR, "risco_folhas.csv"), index=False)
    with open(os.path.join(GOLD_DIR, "acoes_talhao.json"), "w", encoding="utf-8") as f:
        json.dump(acoes, f, indent=2, ensure_ascii=False)

    print(
        f"[automacao] {len(alertas)} alertas de sensor, {len(risco)} folhas classificadas "
        f"({(risco['nivel_risco'] == 'alto').sum()} de risco alto), {len(acoes)} decisoes por talhao."
    )
    return alertas, risco, acoes


if __name__ == "__main__":
    executar()

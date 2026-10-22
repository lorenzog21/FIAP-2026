"""Saude do sistema: status, historico de execucoes, tempo por etapa e log da aplicacao."""
import os
import json
import pandas as pd
import plotly.express as px
import streamlit as st

LOGS = os.path.join("data", "logs")
st.set_page_config(page_title="AgroSmart - Saúde do sistema", page_icon="🩺", layout="wide")

st.sidebar.title("🍎 AgroSmart")
limite_min = st.sidebar.number_input("Dados considerados desatualizados após (min)", 1, 1440, 15)
atualizar = st.sidebar.toggle("Atualizar a cada 10 s", value=True)

st.title("Saúde do sistema")
st.caption("Monitoramento do pipeline: cada execução registra status, duração por etapa e contagens "
           "em `data/logs/execucoes.jsonl`; o log da aplicação está em `data/logs/app.log`.")


def carregar():
    caminho = os.path.join(LOGS, "execucoes.jsonl")
    if not os.path.exists(caminho):
        return pd.DataFrame()
    with open(caminho, encoding="utf-8") as f:
        linhas = [json.loads(linha_) for linha_ in f if linha_.strip()]
    df = pd.DataFrame(linhas)
    # ISO8601 aceita registros antigos (sem fuso) e novos (+00:00) no mesmo arquivo
    df["inicio"] = pd.to_datetime(df["inicio"], utc=True, format="ISO8601")
    df["fim"] = pd.to_datetime(df["fim"], utc=True, format="ISO8601")
    return df


def painel():
    df = carregar()
    if df.empty:
        st.warning("Nenhuma execução registrada. Rode `python appleAnalisys.py` (ou `docker compose up`).")
        return
    ult = df.iloc[-1]
    idade_min = (pd.Timestamp.now(tz="UTC") - ult["fim"]).total_seconds() / 60
    if ult["status"] != "sucesso":
        estado, cor = "FALHA", "🔴"
    elif idade_min > limite_min:
        estado, cor = "DADOS DESATUALIZADOS", "🟡"
    else:
        estado, cor = "OPERACIONAL", "🟢"
    st.subheader(f"{cor} {estado}")

    c = st.columns(5)
    c[0].metric("Última execução", f"{idade_min:.0f} min atrás" if idade_min >= 1 else "agora",
                help=f"{ult['inicio']:%d/%m %H:%M:%S} UTC")
    c[1].metric("Duração", f"{ult['duracao_s']:.1f} s", help=f"modo: {ult['modo']}")
    c[2].metric("Taxa de sucesso", f"{(df['status'] == 'sucesso').mean():.0%}", f"{len(df)} execuções", delta_color="off")
    c[3].metric("Alertas de sensor", int(ult.get("alertas_sensor", 0) or 0))
    anom = ult.get("leituras_anomalas", 0) or 0
    tot = ult.get("leituras_sensor", 0) or 1
    c[4].metric("Leituras anômalas", f"{anom / tot:.1%}", f"{int(anom)} de {int(tot)}", delta_color="off")

    esq, dir_ = st.columns(2)
    with esq:
        st.markdown("**Duração por execução**")
        d = df.assign(execução=range(1, len(df) + 1))
        fig = px.bar(d, x="execução", y="duracao_s", color="modo", hover_data=["run_id", "status"],
                     labels={"duracao_s": "segundos"}, color_discrete_map={"completo": "#8a5a34", "cache_silver": "#2f7dc1"})
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
    with dir_:
        st.markdown("**Tempo por etapa (média por modo)**")
        etapas = pd.DataFrame([{"modo": r["modo"], **e} for _, r in df.iterrows() for e in r["etapas"]])
        media = etapas.groupby(["atividade", "modo"], as_index=False)["duracao_s"].mean()
        fig = px.bar(media, x="duracao_s", y="atividade", color="modo", orientation="h", barmode="group",
                     labels={"duracao_s": "segundos", "atividade": ""},
                     color_discrete_map={"completo": "#8a5a34", "cache_silver": "#2f7dc1"})
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Últimas execuções**")
    cols = ["run_id", "inicio", "duracao_s", "status", "modo", "seed", "alertas_sensor", "leituras_anomalas",
            "folhas_risco_medio", "folhas_risco_alto"]
    st.dataframe(df[[c_ for c_ in cols if c_ in df]].iloc[::-1].head(15), use_container_width=True, hide_index=True)

    st.markdown("**Log da aplicação (últimos eventos)**")
    log = os.path.join(LOGS, "app.log")
    if os.path.exists(log):
        with open(log, encoding="utf-8") as f:
            eventos = [json.loads(linha_) for linha_ in f.readlines()[-300:] if linha_.strip()]
        ev = pd.DataFrame(eventos)
        niveis = st.multiselect("Nível", sorted(ev["nivel"].unique()), default=sorted(ev["nivel"].unique()))
        st.dataframe(ev[ev["nivel"].isin(niveis)].iloc[::-1].head(40), use_container_width=True, hide_index=True)


if atualizar:
    st.fragment(painel, run_every=10)()
else:
    painel()

"""
Fase 6 - Dashboard analitico AgroSmart (Streamlit + Plotly).

Rodar:  streamlit run dashboard.py
Le somente a camada Gold (data/gold/), gerada por `python appleAnalisys.py`.
"""
import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

GOLD = os.path.join("data", "gold")
TEST_DIR = "test"

COR_NIVEL = {"Baixo": "#2e9e5b", "Médio": "#e0a21a", "Alto": "#d64545"}
COR_SEV = {"Média": "#e0a21a", "Alta": "#d64545"}
ROTULO = {"baixo": "Baixo", "medio": "Médio", "alto": "Alto", "alta": "Alta", "media": "Média", "baixa": "Baixa"}
ROTULO_TIPO = {"RISCO_FUNGICO": "Risco fúngico", "SOLO_SECO": "Solo seco",
               "SOLO_ENCHARCADO": "Solo encharcado", "CALOR_EXTREMO": "Calor extremo"}
COR_CLASSE = {"Apple___healthy": "#2e9e5b", "Apple___Black_rot": "#8a4b2b"}
ROTULO_CLASSE = {"Apple___healthy": "Saudável", "Apple___Black_rot": "Black Rot"}
VARIAVEIS = {
    "temperatura_c": ("Temperatura (°C)", "#d6702e"),
    "umidade_ar_pct": ("Umidade do ar (%)", "#2f7dc1"),
    "umidade_solo_pct": ("Umidade do solo (%)", "#7a5a3a"),
    "luminosidade_pct": ("Luminosidade (%)", "#c9a400"),
}

st.set_page_config(page_title="AgroSmart - Dashboard", page_icon="🍎", layout="wide")


@st.cache_data
def carregar():
    sensores = pd.read_csv(os.path.join(GOLD, "dataset_dashboard.csv"), parse_dates=["timestamp"])
    diag = pd.read_csv(os.path.join(GOLD, "diagnosticos.csv"))
    risco = pd.read_csv(os.path.join(GOLD, "risco_folhas.csv"))
    alertas = pd.read_csv(os.path.join(GOLD, "alertas.csv"), parse_dates=["inicio", "fim"])
    with open(os.path.join(GOLD, "acoes_talhao.json"), encoding="utf-8") as f:
        acoes = pd.DataFrame(json.load(f))
    with open(os.path.join(GOLD, "insights.json"), encoding="utf-8") as f:
        insights = {i["entrada"]["image"]: i["diagnostico_gerado"] for i in json.load(f)}
    return sensores, diag, risco, alertas, acoes, insights


if not os.path.exists(os.path.join(GOLD, "acoes_talhao.json")):
    st.error("Camada Gold não encontrada. Rode `python appleAnalisys.py` primeiro.")
    st.stop()

sensores, diag, risco, alertas, acoes, insights = carregar()

# Rótulos de exibição (os arquivos Gold mantêm os códigos sem acento)
risco = risco.assign(nivel_risco=risco["nivel_risco"].map(ROTULO))
alertas = alertas.assign(severidade=alertas["severidade"].map(ROTULO), tipo=alertas["tipo"].map(ROTULO_TIPO))
acoes = acoes.assign(prioridade=acoes["prioridade"].map(ROTULO))

# ---------- Filtros ----------
st.sidebar.title("🍎 AgroSmart")
talhoes = sorted(sensores["talhao_id"].unique())
sel = st.sidebar.multiselect("Talhões", talhoes, default=talhoes)
sev_sel = st.sidebar.multiselect("Severidade dos alertas", ["Alta", "Média"], default=["Alta", "Média"])
st.sidebar.divider()
st.sidebar.caption(
    f"**Período:** {sensores['timestamp'].min():%d/%m %H:%M} a {sensores['timestamp'].max():%d/%m %H:%M}  \n"
    "**Fontes:** sensores simulados e diagnóstico de folhas por imagem (Random Forest)."
)

s = sensores[sensores["talhao_id"].isin(sel)]
r = risco[risco["talhao_id"].isin(sel)]
a = alertas[alertas["talhao_id"].isin(sel) & alertas["severidade"].isin(sev_sel)]
ac = acoes[acoes["talhao_id"].isin(sel)]

st.title("AgroSmart — Monitoramento e apoio à decisão")
st.caption("Podridão Negra (Black Rot) em macieiras: sensores do ambiente + análise de folhas por imagem.")

# ---------- KPIs ----------
doentes = r[r["classe_prevista"] == "Apple___Black_rot"]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Leituras de sensor", f"{len(s):,}".replace(",", "."))
c2.metric("Folhas analisadas", len(r))
c3.metric("Com Black Rot", f"{len(doentes)}", f"{len(doentes) / max(len(r), 1):.0%} do total", delta_color="off")
c4.metric("Risco ambiental médio", f"{s['risco_ambiental'].mean():.2f}", help="Índice 0–1 combinando umidade do ar, temperatura e umidade do solo.")
c5.metric("Alertas de severidade alta", int((a["severidade"] == "Alta").sum()))

# ---------- Valores atuais e médias ----------
st.subheader("Ambiente: valor atual e média")
ultimo = s[s["timestamp"] == s["timestamp"].max()]
cols = st.columns(4)
for col, (campo, (titulo, _)) in zip(cols, VARIAVEIS.items()):
    atual, media = ultimo[campo].mean(), s[campo].mean()
    col.metric(titulo, f"{atual:.1f}", f"{atual - media:+.1f} vs média ({media:.1f})", delta_color="off",
               help=f"Atual = leitura mais recente ({s['timestamp'].max():%d/%m %H:%M}), média entre os talhões "
                    f"selecionados. Média = todas as leituras do período. Min {s[campo].min():.1f} · máx {s[campo].max():.1f}.")

st.caption(f"Atual = leitura mais recente ({s['timestamp'].max():%d/%m %H:%M}), média entre os talhões selecionados; "
           "a luminosidade cai a zero à noite.")

# ---------- Decisão por talhão ----------
st.subheader("Decisão recomendada por talhão")
cols = st.columns(max(len(ac), 1))
prioridade_cor = {"Alta": "🔴", "Média": "🟡", "Baixa": "🟢"}
for col, (_, linha) in zip(cols, ac.iterrows()):
    with col:
        with st.container(border=True, height=340):
            st.markdown(f"**Talhão {linha['talhao_id']}** {prioridade_cor[linha['prioridade']]} prioridade {linha['prioridade'].lower()}")
            st.caption(f"{linha['folhas_com_black_rot']} de {linha['folhas_analisadas']} folhas com Black Rot · {linha['alertas_sensor']} alertas de sensor")
            st.write(linha["decisao"])

# ---------- Séries temporais ----------
st.subheader("Evolução dos sensores")
tabs = st.tabs([v[0] for v in VARIAVEIS.values()])
for tab, (campo, (titulo, cor)) in zip(tabs, VARIAVEIS.items()):
    with tab:
        fig = go.Figure()
        for t in sel:
            d = s[s["talhao_id"] == t]
            fig.add_trace(go.Scatter(x=d["timestamp"], y=d[campo], mode="lines", name=t))
            corrigidos = d[d["valor_imputado"]]
            if len(corrigidos):
                fig.add_trace(go.Scatter(
                    x=corrigidos["timestamp"], y=corrigidos[campo], mode="markers",
                    marker=dict(symbol="x", size=9, color="#d64545"),
                    name=f"{t} (corrigido)", showlegend=False,
                    hovertemplate="Leitura anômala corrigida por interpolação<extra></extra>"))
        if campo == "umidade_ar_pct":
            fig.add_hline(y=75, line_dash="dot", annotation_text="limiar de risco (75%)")
        if campo == "umidade_solo_pct":
            fig.add_hline(y=30, line_dash="dot", annotation_text="irrigar (<30%)")
        fig.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0), yaxis_title=titulo, legend_title="Talhão")
        st.plotly_chart(fig, use_container_width=True)
st.caption("✕ vermelho = leitura anômala do sensor, corrigida por interpolação (rastreável na coluna `valor_imputado`).")

# ---------- Risco ambiental ----------
left, right = st.columns([3, 2])
with left:
    st.subheader("Risco ambiental por hora do dia")
    heat = s.groupby(["talhao_id", "hora"])["risco_ambiental"].mean().reset_index()
    fig = px.density_heatmap(heat, x="hora", y="talhao_id", z="risco_ambiental", histfunc="avg",
                             color_continuous_scale=["#e8f5ec", "#e0a21a", "#d64545"], range_color=[0, 1],
                             nbinsx=24)
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), coloraxis_colorbar_title="Risco")
    fig.update_xaxes(title="Hora do dia", dtick=3)
    fig.update_yaxes(title="Talhão", type="category")
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("Saudável × Black Rot por talhão")
    cont = r.groupby(["talhao_id", "classe_prevista"]).size().reset_index(name="folhas")
    cont["classe"] = cont["classe_prevista"].map(ROTULO_CLASSE)
    fig = px.bar(cont, x="talhao_id", y="folhas", color="classe_prevista", barmode="stack",
                 color_discrete_map=COR_CLASSE, labels={"talhao_id": "Talhão", "folhas": "Folhas"})
    fig.for_each_trace(lambda t: t.update(name=ROTULO_CLASSE[t.name]))
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), legend_title="")
    fig.update_xaxes(type="category", title="Talhão")
    st.plotly_chart(fig, use_container_width=True)

# ---------- Folhas ----------
st.subheader("Folhas analisadas")
f1, f2 = st.columns([2, 3])
with f1:
    fig = px.scatter(r, x="area_infectada_pct", y="indice_risco", color="nivel_risco",
                     color_discrete_map=COR_NIVEL, hover_name="imagem",
                     labels={"area_infectada_pct": "Área infectada (%)", "indice_risco": "Índice de risco (0–1)",
                             "nivel_risco": "Nível"},
                     category_orders={"nivel_risco": ["Baixo", "Médio", "Alto"]})
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
with f2:
    top = r.sort_values("indice_risco", ascending=False).head(5)
    st.markdown("**Maior risco**")
    for _, linha in top.iterrows():
        ca, cb = st.columns([1, 4])
        caminho = os.path.join(TEST_DIR, linha["imagem"])
        if os.path.exists(caminho):
            ca.image(caminho, use_container_width=True)
        cb.markdown(f"**{linha['imagem']}** · talhão {linha['talhao_id']} · risco **{linha['nivel_risco']}** ({linha['indice_risco']:.2f})")
        cb.caption(insights.get(linha["imagem"], ""))

with st.expander("Tabela completa de folhas e ações recomendadas"):
    st.dataframe(
        r.sort_values("indice_risco", ascending=False).drop(columns=["classe_prevista"]),
        use_container_width=True, hide_index=True,
        column_config={"imagem": "Imagem", "talhao_id": "Talhão", "area_infectada_pct": st.column_config.NumberColumn("Área infectada (%)", format="%.1f"),
                       "indice_risco": st.column_config.ProgressColumn("Índice de risco", min_value=0, max_value=1, format="%.2f"),
                       "nivel_risco": "Nível", "fatores_ambientais": "Fatores ambientais", "acao_recomendada": "Ação recomendada"})

# ---------- Alertas ----------
st.subheader("Alertas e recomendações automáticas")
if a.empty:
    st.info("Nenhum alerta para os filtros selecionados.")
else:
    a = a.assign(duracao_h=((a["fim"] - a["inicio"]).dt.total_seconds() / 3600 + 1).round(0).astype(int))
    por_tipo = a.groupby(["tipo", "severidade"]).size().reset_index(name="episodios")
    fig = px.bar(por_tipo, x="episodios", y="tipo", color="severidade", orientation="h",
                 color_discrete_map=COR_SEV, labels={"tipo": "", "episodios": "Episódios"})
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        a.sort_values(["severidade", "inicio"], ascending=[True, True])[
            ["talhao_id", "tipo", "severidade", "inicio", "duracao_h", "descricao", "recomendacao"]
        ],
        use_container_width=True, hide_index=True,
        column_config={"talhao_id": "Talhão", "tipo": "Alerta", "severidade": "Severidade",
                       "inicio": st.column_config.DatetimeColumn("Início", format="DD/MM HH:mm"),
                       "duracao_h": st.column_config.NumberColumn("Duração (h)"),
                       "descricao": "Condição", "recomendacao": "Ação recomendada"},
    )

# ---------- Alertas ao vivo ----------
st.subheader("Alertas ao vivo (demo)")
st.caption("Rode `python demo_alerta_ao_vivo.py` em outro terminal: os alertas aparecem aqui em tempo real.")
ARQ_VIVO = os.path.join(GOLD, "alertas_ao_vivo.jsonl")


@st.fragment(run_every=2)
def painel_ao_vivo():
    if not os.path.exists(ARQ_VIVO) or os.path.getsize(ARQ_VIVO) == 0:
        st.info("Aguardando alertas... (nenhum disparado ainda)")
        return
    vivo = pd.read_json(ARQ_VIVO, lines=True).sort_index(ascending=False)
    vivo = vivo.assign(tipo=vivo["tipo"].map(ROTULO_TIPO), severidade=vivo["severidade"].str.lower().map(ROTULO))
    st.dataframe(vivo[["hora", "talhao_id", "tipo", "severidade", "recomendacao"]],
                 use_container_width=True, hide_index=True,
                 column_config={"hora": "Hora", "talhao_id": "Talhão", "tipo": "Alerta",
                                "severidade": "Severidade", "recomendacao": "Ação recomendada"})


painel_ao_vivo()

# ---------- Fluxo simulado de sensores ----------
SERIAL = os.path.join("data", "silver", "sensores_stream.csv")
if os.path.exists(SERIAL):
    with st.expander("Fluxo simulado de sensores — leituras a cada 2 s (amostra processada)"):
        tc = pd.read_csv(SERIAL)
        longo = tc.melt(id_vars="t_ms", value_vars=list(VARIAVEIS), var_name="sensor", value_name="valor")
        longo["sensor"] = longo["sensor"].map({k: v[0] for k, v in VARIAVEIS.items()})
        fig = px.line(longo, x="t_ms", y="valor", color="sensor", labels={"t_ms": "tempo (ms)", "valor": ""})
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(tc)} leituras · arquivo(s): {', '.join(sorted(tc['arquivo'].unique()))}")

"""
Analise de processo (mineracao de processos) do AgroSmart, a partir dos event logs
gerados pelo proprio pipeline (observabilidade.py):

  data/logs/event_log_execucoes.csv   caso = execucao do pipeline,   atividade = etapa
  data/logs/event_log_folhas.csv      caso = folha em uma execucao,  atividade = passo sobre a folha

Saidas em data/analise/ (nada e escrito a mao; tudo vem do log):
  dfg_execucoes.svg, dfg_folhas.svg     grafo de fluxo (directly-follows) com frequencia e tempos
  metricas_execucoes.csv, metricas_folhas.csv, variantes_execucoes.csv, variantes_folhas.csv
  relatorio_processo.md                 numeros e insights

Uso: python analise_processo.py
"""
import os
import json
import html
from collections import Counter, defaultdict

import pandas as pd

LOGS = os.path.join("data", "logs")
SAIDA = os.path.join("data", "analise")


# ---------------------------------------------------------------- carga
def carregar():
    """Considera so execucoes FINALIZADAS (presentes em execucoes.jsonl); uma execucao em andamento
    ou interrompida nao tem resumo e distorceria as variantes."""
    with open(os.path.join(LOGS, "execucoes.jsonl"), encoding="utf-8") as f:
        runs = pd.DataFrame([json.loads(linha) for linha in f if linha.strip()])
    runs["versao"] = runs["versao"].fillna("1.0") if "versao" in runs else "1.0"
    excl = os.path.join(LOGS, "runs_excluidas.txt")
    if os.path.exists(excl):  # execucoes invalidadas de forma documentada (ver o arquivo)
        with open(excl, encoding="utf-8") as f:
            ignoradas = {linha.split("#")[0].strip() for linha in f if linha.strip() and not linha.startswith("#")}
        runs = runs[~runs["run_id"].isin(ignoradas)]
    ex = pd.read_csv(os.path.join(LOGS, "event_log_execucoes.csv"))
    fo = pd.read_csv(os.path.join(LOGS, "event_log_folhas.csv"))
    for df in (ex, fo):   # UTC; registros antigos sem fuso tambem estavam em UTC
        for c in ("inicio", "fim"):
            df[c] = pd.to_datetime(df[c], utc=True, format="mixed")
    ex = ex[ex["case_id"].isin(runs["run_id"])]
    fo = fo[fo["run_id"].isin(runs["run_id"])]
    # ordem de gravacao = ordem real dos eventos (horarios empatam no log antigo, em milissegundos)
    return ex.sort_values("case_id", kind="stable"), fo.sort_values("case_id", kind="stable"), runs


# ---------------------------------------------------------------- metricas
def metricas_atividades(df):
    g = df.groupby("atividade")["duracao_s"]
    m = pd.DataFrame({
        "ocorrencias": g.count(), "media_s": g.mean(), "mediana_s": g.median(),
        "p95_s": g.quantile(0.95), "total_s": g.sum(),
    })
    m["pct_do_tempo_total"] = (m["total_s"] / m["total_s"].sum() * 100).round(1)
    m["erros"] = df[df["resultado"] == "erro"].groupby("atividade").size().reindex(m.index).fillna(0).astype(int)
    return m.sort_values("total_s", ascending=False).round(4)


def variantes(df):
    caminhos = df.groupby("case_id", sort=False).apply(
        lambda c: " > ".join(c["atividade"]), include_groups=False)
    dur = df.groupby("case_id").apply(
        lambda c: (c["fim"].max() - c["inicio"].min()).total_seconds(), include_groups=False)
    t = pd.DataFrame({"variante": caminhos, "duracao_total_s": dur})
    v = t.groupby("variante").agg(casos=("duracao_total_s", "count"), duracao_media_s=("duracao_total_s", "mean"))
    v["pct_dos_casos"] = (v["casos"] / v["casos"].sum() * 100).round(1)
    return v.sort_values("casos", ascending=False).round(4).reset_index()


def esperas(df):
    """Tempo entre o fim de uma atividade e o inicio da seguinte (mesmo caso)."""
    ev = df.copy()
    ev["prox_inicio"] = ev.groupby("case_id")["inicio"].shift(-1)
    ev["espera_s"] = (ev["prox_inicio"] - ev["fim"]).dt.total_seconds()
    return ev.dropna(subset=["espera_s"])


# ---------------------------------------------------------------- DFG
def dfg(df):
    arestas = Counter()
    for _, c in df.groupby("case_id", sort=False):
        atv = list(c["atividade"])
        for a, b in zip(atv, atv[1:], strict=False):
            arestas[(a, b)] += 1
    return arestas


def camadas(arestas, atividades):
    prof = {a: 0 for a in atividades}
    for _ in range(len(atividades)):  # relaxamento (grafo praticamente aciclico)
        mudou = False
        for (a, b) in arestas:
            if prof[b] < prof[a] + 1 and prof[a] + 1 < len(atividades):
                prof[b] = prof[a] + 1
                mudou = True
        if not mudou:
            break
    return prof


def _cor(frac):
    # amarelo claro -> vermelho conforme a fracao do tempo
    r = 255
    g = int(245 - 150 * frac)
    b = int(220 - 190 * frac)
    return f"#{r:02x}{max(g, 0):02x}{max(b, 0):02x}"


def desenhar_dfg(df, metricas, titulo, caminho):
    arestas = dfg(df)
    atividades = list(metricas.index)
    prof = camadas(arestas, atividades)
    colunas = defaultdict(list)
    for a in sorted(atividades, key=lambda x: (prof[x], -metricas.loc[x, "ocorrencias"])):
        colunas[prof[a]].append(a)
    pos = {}
    for d, nomes in colunas.items():
        for i, a in enumerate(nomes):
            pos[a] = (40 + d * 235, 95 + i * 105)
    largura = 40 + (max(colunas) + 1) * 235
    altura = 95 + max(len(v) for v in colunas.values()) * 105 + 50
    total = metricas["total_s"].sum()
    gargalo = metricas["total_s"].idxmax()
    esp = esperas(df)
    espera_media = esp.groupby(["atividade"])["espera_s"].mean()
    out = [f'<svg viewBox="0 0 {largura} {altura}" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica,Arial,sans-serif">',
           '<defs><marker id="s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
           '<path d="M0 0L10 5L0 10z" fill="#334155"/></marker></defs>',
           f'<rect width="{largura}" height="{altura}" fill="#f8fafc"/>',
           f'<text x="{largura / 2}" y="30" text-anchor="middle" font-size="18" font-weight="700" fill="#0f172a">{html.escape(titulo)}</text>',
           f'<text x="{largura / 2}" y="50" text-anchor="middle" font-size="12" fill="#64748b">'
           f'cor = % do tempo total · borda vermelha = gargalo ({html.escape(gargalo)}) · setas = nº de passagens</text>']
    maxc = max(arestas.values()) if arestas else 1
    for (a, b), n in arestas.items():
        x1, y1 = pos[a][0] + 195, pos[a][1] + 32
        x2, y2 = pos[b][0], pos[b][1] + 32
        if x2 <= x1:  # mesma coluna / laco: curva por baixo
            out.append(f'<path d="M{x1 - 100} {y1 + 32} C{x1 - 100} {y1 + 60},{x2 + 100} {y2 + 60},{x2 + 100} {y2 + 32}" '
                       f'fill="none" stroke="#334155" stroke-width="1.5" marker-end="url(#s)"/>')
            continue
        mx = (x1 + x2) / 2
        w = 1 + 3 * n / maxc
        out.append(f'<path d="M{x1} {y1} C{mx} {y1},{mx} {y2},{x2} {y2}" fill="none" stroke="#334155" '
                   f'stroke-width="{w:.1f}" marker-end="url(#s)"/>')
        out.append(f'<text x="{mx}" y="{(y1 + y2) / 2 - 6}" text-anchor="middle" font-size="11" fill="#0f172a" '
                   f'paint-order="stroke" stroke="#f8fafc" stroke-width="3">{n}×</text>')
    for a, (x, y) in pos.items():
        m = metricas.loc[a]
        frac = m["total_s"] / total
        borda = "#d64545" if a == gargalo else "#94a3b8"
        sw = 3 if a == gargalo else 1.2
        out.append(f'<rect x="{x}" y="{y}" width="195" height="64" rx="10" fill="{_cor(frac)}" stroke="{borda}" stroke-width="{sw}"/>')
        out.append(f'<text x="{x + 97}" y="{y + 24}" text-anchor="middle" font-size="12.5" font-weight="700" fill="#0f172a">{html.escape(a)}</text>')
        out.append(f'<text x="{x + 97}" y="{y + 42}" text-anchor="middle" font-size="11" fill="#334155">'
                   f'{int(m["ocorrencias"])}× · média {m["media_s"] * 1000:.1f} ms</text>')
        out.append(f'<text x="{x + 97}" y="{y + 57}" text-anchor="middle" font-size="11" fill="#334155">{m["pct_do_tempo_total"]:.1f}% do tempo</text>')
    out.append("</svg>")
    open(caminho, "w", encoding="utf-8").write("\n".join(out))
    return gargalo, espera_media


# ---------------------------------------------------------------- relatorio
def md_tabela(df, formato=None):
    df = df.reset_index() if df.index.name else df
    linhas = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    for _, r in df.iterrows():
        linhas.append("| " + " | ".join(str(round(v, 3)) if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(linhas)


def main():
    os.makedirs(SAIDA, exist_ok=True)
    ex, fo, runs = carregar()

    # ---- nivel execucao
    m_ex = metricas_atividades(ex)
    v_ex = variantes(ex)
    m_ex.to_csv(os.path.join(SAIDA, "metricas_execucoes.csv"))
    v_ex.to_csv(os.path.join(SAIDA, "variantes_execucoes.csv"), index=False)
    gargalo_ex, _ = desenhar_dfg(ex, m_ex, "Processo de execução do pipeline (caso = execução)",
                                 os.path.join(SAIDA, "dfg_execucoes.svg"))

    # ---- nivel folha
    m_fo = metricas_atividades(fo)
    v_fo = variantes(fo)
    m_fo.to_csv(os.path.join(SAIDA, "metricas_folhas.csv"))
    v_fo.to_csv(os.path.join(SAIDA, "variantes_folhas.csv"), index=False)
    gargalo_fo, _ = desenhar_dfg(fo, m_fo, "Processo de análise de cada folha (caso = folha)",
                                 os.path.join(SAIDA, "dfg_folhas.svg"))

    # ---- numeros para os insights
    n_exec = ex["case_id"].nunique()
    n_folhas = fo["case_id"].nunique()
    resumo = ex.groupby("case_id").agg(inicio=("inicio", "min"), fim=("fim", "max"))
    resumo["dur"] = (resumo["fim"] - resumo["inicio"]).dt.total_seconds()
    modo = ex[ex["atividade"].isin(["extracao_features", "carregar_cache_silver"])].groupby("case_id")["atividade"].first()
    resumo["modo"] = modo.map({"extracao_features": "completo", "carregar_cache_silver": "cache_silver"})
    por_modo = resumo.groupby("modo")["dur"].agg(["count", "mean", "median"]).round(3)

    destino = fo[fo["atividade"].isin(["encaminhar_acao_prioritaria", "arquivar_sem_acao_urgente"])]
    pct_acao = (destino["atividade"] == "encaminhar_acao_prioritaria").mean() * 100
    anom = fo[(fo["atividade"] == "associar_sensor") & (fo["resultado"] == "leitura_anomala")]
    pct_anom = len(anom) / max(fo[fo["atividade"] == "associar_sensor"].shape[0], 1) * 100
    por_ativ_fo = m_fo["media_s"].sort_values(ascending=False)
    comparacao = None
    if runs["versao"].nunique() > 1:
        fo_v = fo.merge(runs[["run_id", "versao"]], on="run_id")
        ex_v = ex.merge(runs[["run_id", "versao"]], left_on="case_id", right_on="run_id")
        clas = fo_v[fo_v["atividade"] == "classificar_folha"].groupby("versao")["duracao_s"].mean() * 1000
        pred = ex_v[ex_v["atividade"] == "predicao_teste"].groupby("versao")["duracao_s"].mean()
        dur = runs.groupby(["versao", "modo"])["duracao_s"].mean().unstack()
        comparacao = pd.DataFrame({"execucoes": runs.groupby("versao").size(),
                                   "classificar_folha_ms": clas, "predicao_teste_s": pred}).join(dur.add_prefix("duracao_")).round(3)
    erros = int((ex["resultado"] == "erro").sum() + (fo["resultado"] == "erro").sum())
    esp_ex = esperas(ex)["espera_s"]

    linhas = [
        "# Análise de processo (mineração de processos)",
        "",
        f"Gerado por `analise_processo.py` a partir de {n_exec} execuções do pipeline "
        f"({len(ex)} eventos de etapa) e {n_folhas} casos de folha ({len(fo)} eventos).",
        "",
        "## 1. Processo de execução do pipeline",
        "",
        "![DFG execuções](dfg_execucoes.svg)",
        "",
        "### Métricas por atividade",
        "",
        md_tabela(m_ex),
        "",
        "### Variantes (caminhos distintos)",
        "",
        md_tabela(v_ex),
        "",
        "### Duração total por modo de execução",
        "",
        md_tabela(por_modo),
        "",
        "## 2. Processo de análise de cada folha",
        "",
        "![DFG folhas](dfg_folhas.svg)",
        "",
        md_tabela(m_fo),
        "",
        "### Variantes",
        "",
        md_tabela(v_fo),
        "",
        "## 3. Insights",
        "",
        f"- **Gargalo na execução:** `{gargalo_ex}` concentra {m_ex.loc[gargalo_ex, 'pct_do_tempo_total']:.1f}% do tempo "
        f"acumulado das etapas.",
    ]
    if {"completo", "cache_silver"} <= set(por_modo.index):
        f_, c_ = por_modo.loc["completo", "mean"], por_modo.loc["cache_silver", "mean"]
        linhas.append(f"- **Variação por modo:** a execução completa leva {f_:.2f} s em média e a com cache Silver "
                      f"{c_:.2f} s ({f_ / c_:.1f}× mais rápida); o cache elimina a releitura das imagens de treino.")
    linhas += [
        f"- **Gargalo por folha:** `{gargalo_fo}` é o passo mais lento ({por_ativ_fo.iloc[0] * 1000:.1f} ms em média, "
        f"{m_fo.loc[gargalo_fo, 'pct_do_tempo_total']:.1f}% do tempo), contra {por_ativ_fo.iloc[-1] * 1e6:.0f} µs do mais rápido.",
        f"- **Desfecho das folhas:** {pct_acao:.0f}% das folhas seguem para ação prioritária e "
        f"{100 - pct_acao:.0f}% são arquivadas sem ação urgente.",
        f"- **Retrabalho de dados:** {pct_anom:.1f}% das associações folha-sensor caíram em leitura anômala "
        f"(corrigida na preparação).",
        f"- **Esperas entre etapas:** mediana de {esp_ex.median() * 1000:.1f} ms entre o fim de uma etapa e o início da "
        f"seguinte; o tempo é gasto executando, não esperando.",
        f"- **Falhas registradas:** {erros} eventos com resultado `erro`.",
        "",
        "## 4. Oportunidades de melhoria",
        "",
        "As recomendações abaixo derivam dos números acima; as aplicadas aparecem na seção seguinte.",
        "",
        f"1. **Predição por folha:** `{gargalo_fo}` é o passo dominante por folha. O modelo roda com `n_jobs=-1` mesmo "
        "para uma amostra por vez, e o custo de criar threads supera o da inferência. Fixar `n_jobs=1` na predição ou "
        "predizer em lote.",
        f"2. **Extração de atributos de treino:** quando não há cache, `{'extracao_features'}` domina a execução. "
        "Manter o cache Silver incremental (só extrair imagens novas) ou paralelizar por processo.",
        "3. **Dados de sensor:** a taxa de leituras anômalas é uma métrica de qualidade da fonte; acompanhar no painel de saúde "
        "e alertar quando passar de um limiar.",
        "",
    ]
    if comparacao is not None:
        linhas += ["## 5. Antes e depois da melhoria aplicada", "",
                   "Cada linha é uma versão do pipeline (`VERSAO_PIPELINE`); as métricas vêm dos mesmos event logs.", "",
                   md_tabela(comparacao), ""]
        v = sorted(comparacao.index)
        a, d = comparacao.loc[v[0]], comparacao.loc[v[-1]]
        if a["classificar_folha_ms"] > 0:
            linhas.append(f"`classificar_folha` caiu de {a['classificar_folha_ms']:.1f} ms para {d['classificar_folha_ms']:.1f} ms por folha "
                          f"({a['classificar_folha_ms'] / max(d['classificar_folha_ms'], 1e-9):.1f}× mais rápido) e a etapa "
                          f"`predicao_teste` de {a['predicao_teste_s']:.2f} s para {d['predicao_teste_s']:.2f} s.")
            linhas.append("")
        if {"duracao_completo", "duracao_cache_silver"} <= set(comparacao.columns):
            fa, fd = a["duracao_completo"], d["duracao_completo"]
            ca, cd = a["duracao_cache_silver"], d["duracao_cache_silver"]
            linhas.append(f"No modo com cache Silver a execução passou de {ca:.2f} s para {cd:.2f} s. No modo completo foi de "
                          f"{fa:.2f} s para {fd:.2f} s: " + ("houve ganho." if fd < fa * 0.95 else
                          "não houve ganho relevante, porque a extração de atributos das imagens de treino domina a execução "
                          "completa (ver seção 3); a melhoria atacou outro gargalo."))
            linhas.append("")
    open(os.path.join(SAIDA, "relatorio_processo.md"), "w", encoding="utf-8").write("\n".join(linhas))
    print(f"[analise] {n_exec} execuções, {n_folhas} folhas -> {SAIDA}/ (gargalo execução: {gargalo_ex}; folha: {gargalo_fo})")


if __name__ == "__main__":
    main()

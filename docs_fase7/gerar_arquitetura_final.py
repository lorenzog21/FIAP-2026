"""
Gera, a partir de arquitetura.toml (fonte unica):
  docs_fase7/arquitetura_final.svg / .png      diagrama
  docs_fase7/01_arquitetura_final.md           descricao dos componentes e do fluxo de dados

Uso (na raiz do projeto):  python docs_fase7/gerar_arquitetura_final.py
O PNG usa o Chrome em modo headless, se existir.
"""
import os
import shutil
import hashlib
import subprocess
import tomllib
from html import escape

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOML = os.path.join(RAIZ, "arquitetura.toml")
SAIDA = os.path.join(RAIZ, "docs_fase7")

CAMADAS = [("fonte", "1 · FONTES DE DADOS", "#2f7dc1"), ("ingestao", "2 · INGESTÃO", "#8a5a34"),
           ("processamento", "3 · PROCESSAMENTO", "#6b7280"), ("decisao", "4 · DECISÃO AUTOMATIZADA", "#c28a00"),
           ("visualizacao", "5 · VISUALIZAÇÃO E MONITORAMENTO", "#2e9e5b")]
COR_PLAT = "#7c3aed"
CW, GAP, X0, Y0 = 270, 60, 30, 135


def carregar():
    with open(TOML, "rb") as f:
        dados = tomllib.load(f)
    return dados["componente"], dados["fluxo"], hashlib.sha256(open(TOML, "rb").read()).hexdigest()[:12]


def altura(c):
    return 60 + 19 * len(c["resumo"]) + 40


def curto(c):
    a = c["arquivos"][0]
    return a if len(a) <= 34 else "…" + a[-33:]


def card(c, x, y, w, cor):
    h = altura(c)
    s = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#fff" stroke="#cbd5e1" stroke-width="1.5"/>',
         f'<path d="M{x} {y + 34} V{y + 12} a12 12 0 0 1 12 -12 H{x + w - 12} a12 12 0 0 1 12 12 V{y + 34} z" fill="{cor}"/>',
         f'<text x="{x + 14}" y="{y + 23}" class="ct">{escape(c["nome"])}</text>']
    yy = y + 58
    for linha in c["resumo"]:
        s.append(f'<text x="{x + 14}" y="{yy}" class="cl">{escape(linha)}</text>')
        yy += 19
    tw = len(curto(c)) * 7 + 18
    s.append(f'<rect x="{x + 14}" y="{y + h - 32}" width="{tw}" height="20" rx="5" fill="#f1f5f9" stroke="#e2e8f0"/>')
    s.append(f'<text x="{x + 22}" y="{y + h - 18}" class="fn">{escape(curto(c))}</text>')
    s.append(f'<text x="{x + w - 12}" y="{y + 23}" text-anchor="end" class="fase">Fase {c["fase"]}</text>')
    return s


def diagrama(comps, fluxos):
    pos = {}  # id -> (x, y, w, h, coluna|None)
    out = []
    ymax = Y0
    for i, (cam, _, cor) in enumerate(CAMADAS):
        x = X0 + i * (CW + GAP)
        y = Y0
        for c in [c for c in comps if c["camada"] == cam]:
            out += card(c, x, y, CW, cor)
            pos[c["id"]] = (x, y, CW, altura(c), i)
            y += altura(c) + 26
        ymax = max(ymax, y)
    # faixa da plataforma
    plat = [c for c in comps if c["camada"] == "plataforma"]
    py = ymax + 55
    larg_total = len(CAMADAS) * CW + (len(CAMADAS) - 1) * GAP
    pw = (larg_total - 20 * (len(plat) - 1)) / len(plat)
    out.append(f'<rect x="{X0 - 12}" y="{py - 40}" width="{larg_total + 24}" height="{max(altura(c) for c in plat) + 62}" '
               f'rx="14" fill="#f5f3ff" stroke="#c4b5fd" stroke-dasharray="6 4"/>')
    out.append(f'<text x="{X0}" y="{py - 18}" class="col" style="fill:{COR_PLAT}">PLATAFORMA · EMPACOTA, VALIDA, OBSERVA E ANALISA O SISTEMA</text>')
    for i, c in enumerate(plat):
        x = X0 + i * (pw + 20)
        out += card(c, x, py, pw, COR_PLAT)
        pos[c["id"]] = (x, py, pw, altura(c), None)
    altura_total = py + max(altura(c) for c in plat) + 120

    # cabecalhos de coluna
    for i, (_, rot, _) in enumerate(CAMADAS):
        out.append(f'<text x="{X0 + i * (CW + GAP)}" y="88" class="col">{escape(rot)}</text>')

    # portas: espalha pontos de saida/entrada ao longo da lateral do cartao (evita linhas empilhadas)
    def centro_y(i):
        return pos[i][1] + pos[i][3] / 2
    saidas, entradas = {}, {}
    for n, f in enumerate(fluxos):
        saidas.setdefault(f["de"], []).append(n)
        entradas.setdefault(f["para"], []).append(n)
    y_saida, y_entrada = {}, {}
    for i, lista in saidas.items():
        lista.sort(key=lambda n: centro_y(fluxos[n]["para"]))
        for r, n in enumerate(lista):
            y_saida[n] = pos[i][1] + pos[i][3] * (r + 1) / (len(lista) + 1)
    for i, lista in entradas.items():
        lista.sort(key=lambda n: centro_y(fluxos[n]["de"]))
        for r, n in enumerate(lista):
            y_entrada[n] = pos[i][1] + pos[i][3] * (r + 1) / (len(lista) + 1)

    # arestas
    canal = {}   # coluna destino -> contador (desloca canais verticais)
    lane = 0
    setas = []
    for n, f in enumerate(fluxos, start=1):
        idx = n - 1
        sx, sy, sw, sh, sc = pos[f["de"]]
        tx, ty, tw, th, tc = pos[f["para"]]
        y1, y2 = y_saida[idx], y_entrada[idx]
        if sc is None:  # origem na faixa da plataforma -> sobe ate o alvo ou segue na faixa
            if tc is None:
                d = f"M{sx + sw} {y1} H{tx}"
                bx, by = (sx + sw + tx) / 2, y1
            else:
                k = canal.get(("plat", tc), 0)
                canal[("plat", tc)] = k + 1
                xin = tx + 40 + 22 * k
                d = f"M{sx + sw / 2} {sy} V{sy - 24 - 6 * k} H{xin} V{ty + th}"
                bx, by = xin, sy - 24 - 6 * k
        elif tc is not None and tc == sc:   # mesma coluna: de baixo para cima do proximo
            xm = sx + sw / 2
            d = f"M{xm} {sy + sh} V{ty}" if ty > sy else f"M{xm} {sy} V{ty + th}"
            bx, by = xm, (sy + sh + ty) / 2
        elif tc - sc == 1:
            k = canal.get(tc, 0)
            canal[tc] = k + 1
            xc = tx - GAP + 14 + 11 * k
            d = f"M{sx + sw} {y1} H{xc} V{y2} H{tx}"
            bx, by = sx + sw + 15, y1
        else:   # salta colunas: corre por uma pista acima dos cartoes
            k = canal.get(tc, 0)
            canal[tc] = k + 1
            ly = 110 + 8 * lane
            lane += 1
            xc = tx - GAP + 14 + 11 * k
            d = f"M{sx + sw} {y1} H{sx + sw + 16 + 7 * lane} V{ly} H{xc} V{y2} H{tx}"
            bx, by = xc, ly
        setas.append(f'<path d="{d}" class="ln"/>')
        setas.append(f'<circle cx="{bx}" cy="{by}" r="10" fill="#0f172a"/><text x="{bx}" y="{by + 4}" class="nb">{n}</text>')
    out += setas

    larg = X0 * 2 + larg_total
    cab = (f'<svg viewBox="0 0 {larg} {altura_total}" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial, sans-serif">'
           '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">'
           '<path d="M0 0L10 5L0 10z" fill="#334155"/></marker><style>'
           '.ct{font-size:15px;font-weight:700;fill:#fff}.cl{font-size:12.5px;fill:#334155}.fase{font-size:11px;fill:#fff;opacity:.85}'
           '.fn{font-size:11.5px;fill:#0f172a;font-family:Menlo,Consolas,monospace}.ln{stroke:#334155;stroke-width:2;fill:none;marker-end:url(#a)}'
           '.nb{font-size:11px;font-weight:700;fill:#fff;text-anchor:middle}.col{font-size:13px;font-weight:700;fill:#475569;letter-spacing:.07em}'
           '.lg{font-size:12.5px;fill:#334155}</style></defs>'
           f'<rect width="{larg}" height="{altura_total}" fill="#f8fafc"/>'
           f'<text x="{larg / 2}" y="40" text-anchor="middle" style="font-size:25px;font-weight:700;fill:#0f172a">AgroSmart · Arquitetura final (Fase 7)</text>'
           f'<text x="{larg / 2}" y="62" text-anchor="middle" style="font-size:13px;fill:#64748b">Entrada (sensores e imagens) → '
           'Data Lake → processamento → decisão automatizada → dashboard; plataforma de containers, CI/CD, observabilidade e mineração de processos</text>')
    rodape = (f'<text x="{X0}" y="{altura_total - 52}" class="lg">Setas numeradas: ver tabela de fluxo em 01_arquitetura_final.md · '
              f'Execução: docker compose up --build  →  http://localhost:8501</text>'
              f'<text x="{X0}" y="{altura_total - 30}" class="lg">Fonte única: arquitetura.toml (este diagrama e a documentação são gerados dele)</text>')
    return cab + "\n".join(out) + rodape + "</svg>"


def markdown(comps, fluxos, h):
    por_id = {c["id"]: c for c in comps}
    nomes_camada = {"fonte": "Fonte de dados", "ingestao": "Ingestão", "processamento": "Processamento",
                    "decisao": "Decisão automatizada", "visualizacao": "Visualização e monitoramento",
                    "plataforma": "Plataforma"}
    m = ["# Arquitetura final da solução AgroSmart", "",
         "> Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · "
         "Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)", "",
         "![Arquitetura final](arquitetura_final.png)", "",
         "Gerado de `arquitetura.toml` por `docs_fase7/gerar_arquitetura_final.py` "
         f"(fonte: `{h}`). Não edite este arquivo à mão.", "",
         "## Componentes", "",
         "| Camada | Componente | Arquivos | Tecnologia | Entradas | Saídas | Fase |", "|---|---|---|---|---|---|---|"]
    for cam in [c[0] for c in CAMADAS] + ["plataforma"]:
        for c in [c for c in comps if c["camada"] == cam]:
            arq = "<br>".join(f"`{a}`" for a in c["arquivos"])
            m.append(f"| {nomes_camada[cam]} | **{c['nome']}** | {arq} | {c['tecnologia']} | {c['entradas']} | {c['saidas']} | {c['fase']} |")
    m += ["", "## Fluxo de dados (setas do diagrama)", "", "| # | De | Para |", "|---|---|---|"]
    for n, f in enumerate(fluxos, start=1):
        m.append(f"| {n} | {por_id[f['de']]['nome']} | {por_id[f['para']]['nome']} |")
    m += ["", "### Em palavras", "",
          "1. **Entrada.** Sensores simulados (fluxo CSV a cada 2 s) e o simulador de talhões (lotes horários com falhas propositais) "
          "gravam no Data Lake **Bronze**, junto com as imagens de folhas catalogadas por talhão.",
          "2. **Processamento.** A visão computacional mede a área doente e o Random Forest classifica a folha; a preparação limpa os "
          "sensores (datas, tipos, ausentes e outliers) e calcula o risco ambiental. Resultados vão para **Silver** e **Gold**.",
          "3. **Decisão.** O motor de regras gera alertas de sensor, classifica o risco de cada folha e decide a ação por talhão; a IA "
          "generativa simulada escreve o diagnóstico; o alerta ao vivo aplica as mesmas regras a cada leitura.",
          "4. **Saída.** O dashboard mostra indicadores, séries, risco, folhas e alertas; a página *Saúde do sistema* mostra o estado do pipeline.",
          "5. **Plataforma.** Tudo roda em containers; o pipeline DevSecOps valida cada mudança; a observabilidade registra logs e o "
          "event log, que a análise de processo transforma em gargalos, variantes e melhorias.", ""]
    return "\n".join(m)


def main():
    comps, fluxos, h = carregar()
    svg = diagrama(comps, fluxos)
    with open(os.path.join(SAIDA, "arquitetura_final.svg"), "w", encoding="utf-8") as f:
        f.write(svg)
    with open(os.path.join(SAIDA, "01_arquitetura_final.md"), "w", encoding="utf-8") as f:
        f.write(markdown(comps, fluxos, h))
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if os.path.exists(chrome):
        import re
        w, hh = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg).groups()
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1.5",
                        f"--window-size={w},{hh}", f"--screenshot={os.path.join(SAIDA, 'arquitetura_final.png')}",
                        "file://" + os.path.join(SAIDA, "arquitetura_final.svg")], capture_output=True)
        destino = os.path.join(RAIZ, "entrega", "fase7", "1_arquitetura")
        if os.path.isdir(destino):
            for ext in ("png", "svg"):
                shutil.copy(os.path.join(SAIDA, f"arquitetura_final.{ext}"), destino)
    print(f"[arquitetura] {len(comps)} componentes, {len(fluxos)} fluxos, fonte {h}")


if __name__ == "__main__":
    main()

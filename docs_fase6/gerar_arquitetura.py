"""Gera arquitetura_fase6.svg (e o PNG, via Chrome headless se disponivel)."""
from xml.sax.saxutils import escape

W, H = 1600, 780
out = []
def add(x): out.append(x)

COR = {"fonte": "#2f7dc1", "bronze": "#8a5a34", "proc": "#6b7280", "decisao": "#c28a00", "viz": "#2e9e5b"}

def card(x, y, w, h, titulo, linhas, cor, arquivo=None):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#fff" stroke="#cbd5e1" stroke-width="1.5"/>')
    add(f'<path d="M{x} {y+34} V{y+12} a12 12 0 0 1 12 -12 H{x+w-12} a12 12 0 0 1 12 12 V{y+34} z" fill="{cor}"/>')
    add(f'<text x="{x+14}" y="{y+23}" class="ct">{escape(titulo)}</text>')
    yy = y + 60
    for texto in linhas:
        add(f'<text x="{x+14}" y="{yy}" class="cl">{escape(texto)}</text>')
        yy += 19
    if arquivo:
        tw = len(arquivo) * 7.2 + 16
        add(f'<rect x="{x+14}" y="{y+h-30}" width="{tw}" height="20" rx="5" fill="#f1f5f9" stroke="#e2e8f0"/>')
        add(f'<text x="{x+22}" y="{y+h-16}" class="fn">{escape(arquivo)}</text>')

def seta(d, n, bx, by):
    add(f'<path d="{d}" class="ln"/>')
    add(f'<circle cx="{bx}" cy="{by}" r="10" fill="#0f172a"/><text x="{bx}" y="{by+4}" class="nb">{n}</text>')

add(f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial, sans-serif">')
add('''<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#334155"/></marker>
<style>.ct{font-size:15px;font-weight:700;fill:#fff}.cl{font-size:12.5px;fill:#334155}.fn{font-size:11.5px;fill:#0f172a;font-family:Menlo,Consolas,monospace}
.ln{stroke:#334155;stroke-width:2;fill:none;marker-end:url(#a)}.nb{font-size:11px;font-weight:700;fill:#fff;text-anchor:middle}
.col{font-size:13px;font-weight:700;fill:#475569;letter-spacing:.08em}.lg{font-size:12.5px;fill:#334155}</style></defs>''')
add(f'<rect width="{W}" height="{H}" fill="#f8fafc"/>')
add(f'<text x="{W/2}" y="40" text-anchor="middle" style="font-size:24px;font-weight:700;fill:#0f172a">AgroSmart · Arquitetura da plataforma (Fase 6)</text>')
add(f'<text x="{W/2}" y="62" text-anchor="middle" style="font-size:13px;fill:#64748b">Da coleta no campo à decisão por talhão: sensores e imagens → Data Lake → processamento → automação → dashboard</text>')

for x, _w, t in [(30, 270, "1 · FONTES DE DADOS"), (370, 260, "2 · INGESTÃO"), (700, 270, "3 · PROCESSAMENTO"),
                (1040, 250, "4 · DECISÃO AUTOMATIZADA"), (1350, 220, "5 · VISUALIZAÇÃO")]:
    add(f'<text x="{x}" y="100" class="col">{t}</text>')

card(30, 115, 270, 175, "Sensores simulados", ["gerador de leituras (2 s)", "temperatura · umidade do solo", "umidade do ar · luminosidade", "saída: CSV (formato Serial)"], COR["fonte"], "simulador_sensores.py")
card(30, 315, 270, 150, "Imagens de folhas", ["drone / câmera manual", "dataset PlantVillage (maçã)", "saudável × Black Rot"], COR["fonte"], "data/ · test/")
card(30, 490, 270, 150, "Simulador de talhões", ["4 talhões, cenários distintos", "mesmo schema do fluxo CSV", "~5% de falhas propositais"], COR["fonte"], "ingest.py")

card(370, 115, 260, 490, "Data Lake · Bronze", ["Dado bruto, exatamente como chegou", "", "sensores/batch_<ts>/*.json", "stream_sensores/*.csv", "metadados_imagens_<ts>.csv", "imagens .JPG", "ingestion_log.jsonl", "", "Append-only, versionado por lote", "Leitura fora de faixa recebe", "flag_anomalia (não é descartada)"], COR["bronze"], "data/bronze/")

card(700, 115, 270, 175, "Visão computacional + ML", ["OpenCV (HSV): % de área doente", "+ circularidade da folha", "Random Forest (scikit-learn)", "→ saudável × Black Rot"], COR["proc"], "appleAnalisys.py")
card(700, 315, 270, 240, "Preparação de dados", ["pandas: datas, tipos, unidades", "ausentes e outliers → interpolação", "valor_imputado preserva rastro", "risco_ambiental (0–1)", "resumo por talhão"], COR["proc"], "processar_dados.py")

card(1040, 115, 250, 185, "Motor de regras", ["4 regras de sensor → alertas", "risco da folha: 70% lesão +", "30% ambiente → baixo/médio/alto", "decisão e ação por talhão"], COR["decisao"], "automacao.py")
card(1040, 330, 250, 180, "IA generativa simulada", ["diagnóstico em linguagem", "natural por folha (templates)", "mesma fórmula de risco"], COR["decisao"], "generate_insights.py")
card(1040, 580, 250, 125, "Alerta ao vivo", ["regras no instante da leitura", "log serial linha a linha"], COR["decisao"], "demo_alerta_ao_vivo.py")

card(1350, 115, 220, 590, "Dashboard analítico", ["Streamlit + Plotly", "", "• valor atual e média", "• decisão por talhão", "• evolução de cada sensor", "• mapa de risco por hora", "• folhas de maior risco", "  (foto + diagnóstico)", "• alertas e recomendações", "• alertas ao vivo", "• amostra do fluxo simulado"], COR["viz"], "dashboard.py")

seta("M300 202 H370", 1, 335, 202)
seta("M300 390 H370", 2, 335, 390)
seta("M300 565 H370", 3, 335, 565)
seta("M630 200 H700", 4, 665, 200)
seta("M630 435 H700", 5, 665, 435)
seta("M835 290 V315", 6, 835, 302)
seta("M970 160 H1040", 7, 1005, 160)
seta("M970 410 H1022 V285 H1040", 8, 990, 410)
seta("M970 255 H1000 V440 H1040", 9, 985, 255)
seta("M1290 217 H1350", 10, 1320, 217)
seta("M1290 420 H1350", 11, 1320, 420)
seta("M1290 642 H1350", 12, 1320, 642)
seta("M500 605 V642 H1040", 13, 770, 642)

add('<g transform="translate(30,730)">')
for i, (c, t) in enumerate([("fonte", "Fonte de dados"), ("bronze", "Data Lake"), ("proc", "Processamento"), ("decisao", "Decisão automatizada"), ("viz", "Visualização")]):
    add(f'<rect x="{i*190}" y="0" width="16" height="16" rx="4" fill="{COR[c]}"/><text x="{i*190+24}" y="13" class="lg">{t}</text>')
add('</g>')
add('<text x="1570" y="743" text-anchor="end" class="lg">Execução: python appleAnalisys.py → streamlit run dashboard.py</text>')
add('<text x="30" y="768" class="lg">1–3 coleta e catalogação · 4–5 leitura do Bronze · 6 diagnósticos para a preparação · 7–9 saídas do ML e dos dados limpos · 10–12 resultados para o dashboard · 13 log serial → alerta ao vivo</text>')
add('</svg>')
open("arquitetura_fase6.svg", "w", encoding="utf-8").write("\n".join(out))
print("svg gerado")

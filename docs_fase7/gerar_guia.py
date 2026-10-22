"""Gera GUIA_DA_ENTREGA.html (3 cores: avaliacao, time, pode tirar) e, em seguida, GUIA_AVALIACAO.html.
Atualizar o guia = editar os dados abaixo e rodar: python docs_fase7/gerar_guia.py"""
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
EQUIPE = ("Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · "
          "Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)")
ROTULO = {"aval": "Para avaliação", "time": "Para o time", "rm": "Pode tirar"}
BADGE = {"ok": '<span class="b ok">pronto</span>', "hum": '<span class="b pend">falta o time (vídeo/link)</span>',
         "ressalva": '<span class="b base">pronto, com ressalva</span>'}


def blk(tipo, titulo, corpo):
    h = (f'<div class="blk {tipo}"><span class="tag">{ROTULO[tipo]}</span>'
         f'{("<h4>" + titulo + "</h4>") if titulo else ""}{corpo}</div>')
    return h if tipo == "aval" else f"<!--CUT:{tipo}-->{h}<!--/CUT-->"


def tabela(linhas):
    t = "<table><tr><th>Artefato exigido</th><th>Onde encontrar</th><th>Status</th></tr>"
    for a, onde, st in linhas:
        t += f"<tr><td>{a}</td><td>{onde}</td><td>{BADGE[st]}</td></tr>"
    return t + "</table>"


C = lambda s: f"<code>{s}</code>"  # noqa: E731

SECOES = [
    ("s1", "1. Arquitetura final da solução",
     blk("aval", "O que é pedido", "<p>Diagrama final com todos os componentes, integração entre serviços, fluxo de dados completo e separação entrada → processamento → saída; descrição dos componentes; explicação do fluxo.</p>")
     + tabela([("Diagrama da arquitetura final", C("docs_fase7/arquitetura_final.png") + " (cópia em " + C("entrega/fase7/1_arquitetura/") + ")", "ok"),
               ("Descrição dos componentes (função, tecnologia, entradas, saídas, fase)", C("docs_fase7/01_arquitetura_final.md") + " (tabela de 15 componentes)", "ok"),
               ("Explicação do fluxo de dados", C("docs_fase7/01_arquitetura_final.md") + " (tabela das 15 setas + texto)", "ok")])
     + blk("aval", "Como a arquitetura é rastreada", "<p>Diagrama e descrição são <b>gerados de um único arquivo</b>, " + C("arquitetura.toml") + ". O " + C("scripts/verificar_entrega.py") + " confere que todo arquivo citado existe, que nenhum código Python fica fora do diagrama, que diagrama e texto estão sincronizados e que o roteiro do vídeo cita cada componente.</p>")
     + blk("time", "Como atualizar", "<pre>python docs_fase7/gerar_arquitetura_final.py   # regenera SVG, PNG e a descrição\npython scripts/verificar_entrega.py             # confere a coerência</pre><p>Para incluir um componente novo, edite só o " + C("arquitetura.toml") + ". Se esquecer, o verificador acusa.</p>")),
    ("s2", "2. Execução da plataforma (sistema funcional)",
     blk("aval", "O que é pedido", "<p>Funcionamento ponta a ponta: entrada de dados, processamento, automação por decisão e saída. Evidências, descrição e exemplo de entrada e saída.</p>")
     + tabela([("Evidências da execução (logs, prints, clipes)", C("entrega/fase7/2_execucao/"), "ok"),
               ("Descrição do funcionamento", C("docs_fase7/02_execucao.md"), "ok"),
               ("Exemplo de entrada e saída", C("docs_fase7/02_execucao.md") + " (dados reais de uma execução)", "ok"),
               ("Execução via container", C("docker compose up --build") + " · " + C("Dockerfile") + ", " + C("docker-compose.yml"), "ok")])
     + blk("time", "Para reproduzir", "<pre>docker compose up --build                                 # pipeline + dashboard\ndocker compose --profile continuo up -d                   # + agendador\ndocker compose --profile demo run --rm alerta-ao-vivo     # alertas ao vivo</pre>")),
    ("s3", "3. Pipeline DevSecOps",
     blk("aval", "O que é pedido", "<p>Build, execução via container, análise de qualidade de código e análise de vulnerabilidades. Arquivos de configuração, descrição e evidência de execução.</p>")
     + tabela([("Dockerfile e docker-compose", C("Dockerfile") + ", " + C("docker-compose.yml"), "ok"),
               ("Pipeline (GitHub Actions) e versão local equivalente", C(".github/workflows/ci.yml") + ", " + C("scripts/ci_local.sh"), "ressalva"),
               ("Qualidade de código (ruff) e testes (pytest)", C("pyproject.toml") + ", " + C("tests/"), "ok"),
               ("Vulnerabilidades (bandit, pip-audit, trivy)", "etapas 5, 6 e 9 do pipeline", "ok"),
               ("Descrição do pipeline", C("docs_fase7/03_devsecops.md"), "ok"),
               ("Evidência da execução", C("entrega/fase7/3_devsecops/evidencias/") + " (resumo, logs e primeira execução com achados)", "ok")])
     + blk("aval", "Resultado", "<p>9 etapas, todas OK na execução final: ruff sem achados, 19 testes, bandit sem achados médios ou altos, pip-audit sem vulnerabilidades, container executado e trivy com 0 vulnerabilidades HIGH/CRITICAL. Na primeira execução o pipeline <b>falhou</b> (MD5 no bandit e variável sem uso no ruff); os achados foram corrigidos e estão documentados.</p>")
     + blk("time", "Ressalvas para saber antes de apresentar", "<ul><li>O " + C("ci.yml") + " <b>não foi executado no GitHub Actions</b>; as mesmas etapas rodaram localmente com Docker, e é isso que as evidências mostram.</li><li>Cobertura de testes de 29%: cobre regras, limpeza, observabilidade e análise; o dashboard foi verificado só no navegador.</li><li>SonarCloud não foi usado (exige conta e token); o requisito de análise estática é atendido por ruff + bandit.</li></ul>")),
    ("s4", "4. Monitoramento e execução automatizada",
     blk("aval", "O que é pedido", "<p>Execução contínua e monitoramento: logs, status de execução e indicadores de funcionamento; descrição e como acompanhar.</p>")
     + tabela([("Logs estruturados e histórico de execuções", C("data/logs/app.log") + ", " + C("data/logs/execucoes.jsonl"), "ok"),
               ("Painel de saúde do sistema", C("pages/1_Saude_do_sistema.py") + " (menu lateral do dashboard)", "ok"),
               ("Execução agendada", "serviço " + C("scheduler") + " do compose, com healthcheck", "ok"),
               ("Prints, logs e clipe do sistema em execução", C("entrega/fase7/4_monitoramento/"), "ok"),
               ("Descrição e como acompanhar", C("docs_fase7/04_monitoramento.md"), "ok")])
     + blk("time", "Detalhe que já nos custou tempo", "<p>O container grava em UTC e o host em horário local; por isso <b>todo horário do log é UTC com fuso explícito</b> (" + C("+00:00") + "). Registros antigos sem fuso são lidos como UTC.</p>")),
    ("s5", "5. Análise de processo e demonstração final",
     blk("aval", "O que é pedido", "<p>Event log, representação do processo, análise de gargalos, variações e oportunidades; vídeo final de 5 a 8 minutos.</p>")
     + tabela([("Exemplo de event log", C("data/logs/event_log_*.csv") + " · amostra em " + C("entrega/fase7/5_processo_e_video_final/event_log_amostra/"), "ok"),
               ("Representação do processo (diagramas)", C("entrega/fase7/5_processo_e_video_final/analise/dfg_*.png"), "ok"),
               ("Análise com insights", C("docs_fase7/05_processo.md") + " e " + C("analise/relatorio_processo.md"), "ok"),
               ("Roteiro do vídeo final (7 min)", C("docs_fase7/roteiro_video_final.md"), "ok"),
               ("Vídeo final (5 a 8 min)", C("entrega/fase7/5_processo_e_video_final/video/LINK.txt"), "hum")])
     + blk("aval", "Principais achados", "<p>Gargalo da execução: extração das imagens (63% do tempo). Gargalo por folha: <code>classificar_folha</code> (94%). Variantes: execução com cache 3,6× mais rápida; 3% das folhas seguem para ação prioritária. Melhoria aplicada: predição por folha de 46 ms para 13 ms (3,7×), medida nos mesmos event logs.</p>")
     + blk("time", "Honestidade da análise", "<p>Não houve execução com falha na base, então a análise não mostra caminhos de erro. A execução <b>completa</b> não ficou mais rápida (o gargalo dela é a extração); isso está escrito no relatório. Duas execuções inválidas foram excluídas em " + C("data/logs/runs_excluidas.txt") + ".</p>")),
    ("s6", "6. Apresentação do produto (pitch)",
     blk("aval", "O que é pedido", "<p>Problema, solução, diferencial, público-alvo e proposta de valor. Slides e vídeo pitch de até 5 minutos.</p>")
     + tabela([("Slides (9, com fala nas notas)", C("entrega/fase7/6_pitch/slides/AgroSmart_Pitch.pptx") + " · imagens em " + C("slides/preview/"), "ok"),
               ("Roteiro do pitch (4 min 50 s)", C("docs_fase7/roteiro_pitch.md"), "ok"),
               ("Vídeo pitch (até 5 min, novo)", C("entrega/fase7/6_pitch/video/LINK.txt"), "hum")])
     + blk("time", "Sobre os slides", "<p>Gerados por " + C("entrega/fase7/6_pitch/gerar_slides.py") + " (python-pptx), com uma prévia em PNG de cada slide. Foram conferidos nas prévias, mas <b>abra o .pptx no PowerPoint e revise</b>: a fonte Calibri/Cambria pode quebrar linhas de forma ligeiramente diferente. As receitas são hipóteses; o slide diz isso.</p>")),
]

MAPA = """<pre>FIAP-2026/
├── arquitetura.toml            fonte única da arquitetura
├── appleAnalisys.py · ingest.py · processar_dados.py · automacao.py · generate_insights.py   pipeline
├── observabilidade.py · analise_processo.py · dashboard.py · pages/ · demo_alerta_ao_vivo.py · simulacao/
├── Dockerfile · docker-compose.yml · .github/workflows/ci.yml · scripts/ (ci_local, status, verificar_entrega…)
├── tests/ · pyproject.toml · requirements*.txt
├── data/{bronze,silver,gold,logs,analise}/
├── docs_fase6/                 documentação da Fase 6
├── docs_fase7/                 guia, checklist, documentos da Fase 7, roteiros
└── entrega/
    ├── IDENTIFICACAO.md
    ├── fase6/{prints,videos,LINK_VIDEO.txt}
    └── fase7/{1_arquitetura, 2_execucao, 3_devsecops, 4_monitoramento, 5_processo_e_video_final, 6_pitch}</pre>"""

PENDENCIAS = ("<ul><li>Gravar o <b>vídeo final</b> (7 min) e o <b>vídeo pitch</b> (até 5 min); colar os links nos <code>LINK.txt</code>; abrir em janela anônima.</li>"
              "<li>Abrir o <code>.pptx</code> no PowerPoint e revisar o texto e as quebras de linha.</li>"
              "<li>Rodar <code>python docs_fase7/gerar_guia.py</code> e <code>python scripts/verificar_entrega.py</code> antes de empacotar.</li>"
              "<li>Rodar <code>./empacotar_fase7.sh</code> e entregar o zip.</li></ul>")

LEGENDA = ('<div class="leg"><span style="background:var(--aval);border-color:var(--avalb)">Azul · explicação para a avaliação (fica na entrega)</span>'
           '<span style="background:var(--time);border-color:var(--timeb)">Amarelo · explicação para o time (sai da entrega)</span>'
           '<span style="background:var(--rm);border-color:var(--rmb)">Vermelho · pode tirar (pendências e rascunhos)</span></div>')

CSS = """:root{--bg:#f7f8fa;--fg:#1f2937;--mut:#6b7280;--aval:#e8f1fb;--avalb:#2f7dc1;--time:#fff6dc;--timeb:#c28a00;--rm:#fdecec;--rmb:#d64545;--ok:#2e9e5b}
@media(prefers-color-scheme:dark){:root{--bg:#111827;--fg:#e5e7eb;--mut:#9ca3af;--aval:#12263a;--time:#33290d;--rm:#3a1717}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,Segoe UI,Helvetica,Arial,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid #8884;padding:12px 24px;z-index:5}
main{max-width:980px;margin:0 auto;padding:16px 24px 80px}h1{margin:0 0 4px;font-size:22px}h2{margin:36px 0 10px;font-size:19px}h4{margin:2px 0 6px}
.team{color:var(--mut);font-size:13px}.ctrl{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
button{border:1px solid #8886;border-radius:8px;padding:5px 10px;background:transparent;color:var(--fg);cursor:pointer;font-size:13px}button.on{background:#8882}
.blk{border-left:5px solid;border-radius:8px;padding:10px 14px;margin:10px 0}.blk p{margin:6px 0}.blk ul{margin:6px 0;padding-left:20px}
.aval{background:var(--aval);border-color:var(--avalb)}.time{background:var(--time);border-color:var(--timeb)}.rm{background:var(--rm);border-color:var(--rmb)}
.tag{float:right;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;opacity:.8}
.aval .tag{color:var(--avalb)}.time .tag{color:var(--timeb)}.rm .tag{color:var(--rmb)}
table{width:100%;border-collapse:collapse;margin:10px 0;font-size:14px}th,td{border:1px solid #8884;padding:6px 9px;text-align:left;vertical-align:top}th{background:#8881}
.b{padding:2px 8px;border-radius:99px;font-size:12px;font-weight:600;white-space:nowrap}.b.ok{background:#2e9e5b33;color:var(--ok)}.b.base{background:#c28a0033;color:var(--timeb)}.b.pend{background:#d6454533;color:var(--rmb)}
code,pre{font-family:Menlo,Consolas,monospace;font-size:13px}code{background:#8882;padding:1px 5px;border-radius:4px}pre{background:#8881;padding:10px;border-radius:8px;overflow:auto}
.leg{display:flex;gap:10px;flex-wrap:wrap;margin:6px 0}.leg span{padding:3px 10px;border-radius:99px;border:1px solid;font-size:12px}
.hide-aval .aval,.hide-time .time,.hide-rm .rm{display:none}
@media print{header .ctrl{display:none}header{position:static}}"""


def main():
    corpo = "".join(f'<h2 id="{i}">{t}</h2>{c}' for i, t, c in SECOES)
    uso = blk("time", "Como usar este guia", "<p>Fonte de verdade da Fase 7: para cada requisito, o que é exigido, onde está o artefato e se está pronto. As cores separam três tipos de texto:</p>" + LEGENDA +
              "<p>Para a versão de avaliação (sem amarelo e vermelho): <code>python docs_fase7/gerar_guia.py</code> gera também <code>GUIA_AVALIACAO.html</code>. O progresso fino está em <code>CHECKLIST_FASE7.md</code>.</p>")
    resumo = blk("aval", "Resumo", "<p>O AgroSmart monitora macieiras contra a Podridão Negra: sensores simulados e fotos de folhas alimentam um Data Lake (Bronze, Silver e Gold); um motor de regras e um modelo de visão computacional geram alertas e decisões por talhão; um dashboard apresenta os resultados. Na Fase 7 a solução ganhou execução em container, pipeline DevSecOps, monitoramento, análise de processo e visão de produto.</p>")
    html = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgroSmart Fase 7 - Guia da entrega</title><style>{CSS}</style></head><body>
<header><h1>AgroSmart · Fase 7 · Guia da entrega</h1><div class="team">{EQUIPE}</div>
<div class="ctrl"><span style="font-size:13px;align-self:center">Mostrar:</span>
<button id="b-aval" class="on" onclick="tog('aval')">Avaliação</button><button id="b-time" class="on" onclick="tog('time')">Time</button>
<button id="b-rm" class="on" onclick="tog('rm')">Pode tirar</button><button onclick="modo()">Modo entrega (só avaliação)</button></div></header>
<main>{uso}{resumo}{corpo}
<h2 id="mapa">Mapa de pastas</h2>{blk("aval", "", MAPA)}
<h2 id="docs">Documentos da Fase 7</h2>{blk("aval", "", "<ul><li><code>docs_fase7/01_arquitetura_final.md</code> arquitetura</li><li><code>02_execucao.md</code> execução</li><li><code>03_devsecops.md</code> pipeline DevSecOps</li><li><code>04_monitoramento.md</code> monitoramento</li><li><code>05_processo.md</code> análise de processo</li><li><code>roteiro_video_final.md</code> e <code>roteiro_pitch.md</code> roteiros dos vídeos</li></ul>")}
<h2 id="pend">O que falta</h2>{blk("rm", "Pendências do time", PENDENCIAS)}
</main>
<script>function tog(k){{document.body.classList.toggle('hide-'+k);document.getElementById('b-'+k).classList.toggle('on')}}
function modo(){{['time','rm'].forEach(k=>{{document.body.classList.add('hide-'+k);document.getElementById('b-'+k).classList.remove('on')}})}}</script></body></html>"""
    with open(os.path.join(AQUI, "GUIA_DA_ENTREGA.html"), "w", encoding="utf-8") as f:
        f.write(html)
    subprocess.run([sys.executable, os.path.join(AQUI, "exportar_guia_avaliacao.py")], check=True)


if __name__ == "__main__":
    main()

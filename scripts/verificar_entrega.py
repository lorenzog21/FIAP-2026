"""
Verifica se a entrega da Fase 7 esta coerente (rastreabilidade):

  1. todo arquivo citado em arquitetura.toml existe
  2. todo codigo Python do projeto pertence a algum componente (sem codigo "orfao" fora do diagrama)
  3. diagrama e descricao de arquitetura estao sincronizados com arquitetura.toml
  4. o roteiro do video final cobre todos os componentes do diagrama
  5. itens marcados [x] no checklist apontam para arquivos que existem
  6. cada pasta de entrega tem conteudo; links de video preenchidos
  7. identificacao da equipe e cabecalho da equipe nos documentos
  8. ultima execucao do pipeline DevSecOps local sem falhas

Uso (na raiz do projeto):  python scripts/verificar_entrega.py
Saida: OK / AVISO (pendencia humana: gravar video, colar link) / ERRO. Codigo 1 se houver ERRO.
"""
import os
import re
import sys
import glob
import importlib.util
import tomllib

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(RAIZ)
resultados = []


def registrar(nivel, grupo, msg):
    resultados.append((nivel, grupo, msg))


def ler(caminho):
    with open(caminho, encoding="utf-8") as f:
        return f.read()


def checar_arquitetura():
    dados = tomllib.load(open("arquitetura.toml", "rb"))
    comps, ignorar = dados["componente"], set(dados.get("ignorar_codigo", []))
    ausentes = [(c["id"], a) for c in comps for a in c["arquivos"] if not os.path.exists(a)]
    for cid, a in ausentes:
        registrar("ERRO", "arquitetura", f"componente '{cid}' cita arquivo inexistente: {a}")
    if not ausentes:
        registrar("OK", "arquitetura", f"{len(comps)} componentes, todos os arquivos citados existem")

    citados = {a for c in comps for a in c["arquivos"]}
    codigo = [p.replace(os.sep, "/") for p in glob.glob("**/*.py", recursive=True)
              if not p.startswith((".venv", "tests", "data", "docs_fase6", "docs_fase7"))]
    orfaos = [p for p in codigo if p not in citados and p not in ignorar]
    for p in orfaos:
        registrar("ERRO", "arquitetura", f"codigo fora do diagrama (adicione a um componente ou a ignorar_codigo): {p}")
    if not orfaos:
        registrar("OK", "arquitetura", "nenhum codigo orfao: todo .py esta em algum componente")
    return comps, dados.get("fluxo", [])


def checar_sincronia(comps, fluxos):
    caminho = os.path.join("docs_fase7", "gerar_arquitetura_final.py")
    spec = importlib.util.spec_from_file_location("gerar_arq", caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _, _, h = mod.carregar()
    esperado_md = mod.markdown(comps, fluxos, h)
    esperado_svg = mod.diagrama(comps, fluxos)
    for nome, esperado in (("01_arquitetura_final.md", esperado_md), ("arquitetura_final.svg", esperado_svg)):
        p = os.path.join("docs_fase7", nome)
        if not os.path.exists(p) or ler(p) != esperado:
            registrar("ERRO", "sincronia", f"{nome} esta desatualizado: rode python docs_fase7/gerar_arquitetura_final.py")
        else:
            registrar("OK", "sincronia", f"{nome} bate com arquitetura.toml (fonte {h})")
    copia = os.path.join("entrega", "fase7", "1_arquitetura", "arquitetura_final.png")
    if os.path.exists(copia) and os.path.exists("docs_fase7/arquitetura_final.png"):
        if open(copia, "rb").read() != open("docs_fase7/arquitetura_final.png", "rb").read():
            registrar("ERRO", "sincronia", "PNG da pasta de entrega difere de docs_fase7/arquitetura_final.png")
    else:
        registrar("ERRO", "sincronia", "diagrama PNG ausente em entrega/fase7/1_arquitetura/")


def checar_video(comps):
    roteiro = os.path.join("docs_fase7", "roteiro_video_final.md")
    if not os.path.exists(roteiro):
        registrar("AVISO", "video", "roteiro_video_final.md ainda nao existe")
        return
    texto = ler(roteiro).lower()
    faltam = [c["nome"] for c in comps if not any(t.lower() in texto for t in c.get("termos", [c["nome"]]))]
    for n in faltam:
        registrar("ERRO", "video", f"roteiro do video final nao cobre o componente: {n}")
    if not faltam:
        registrar("OK", "video", "roteiro do video final cobre todos os componentes do diagrama")


def checar_checklist():
    caminho = os.path.join("docs_fase7", "CHECKLIST_FASE7.md")
    feitos = pendentes = 0
    ruins = []
    for linha in ler(caminho).splitlines():
        m = re.match(r"- \[(x| )\] (.*)", linha)
        if not m:
            continue
        feito, texto = m.group(1) == "x", m.group(2)
        feitos += feito
        pendentes += not feito
        if not feito or "🧑" in texto:
            continue
        for tok in re.findall(r"`([^`]+)`", texto):
            if ("/" in tok or re.search(r"\.(py|md|yml|yaml|toml|txt|csv|png|svg|html|sh|jsonl|json)$", tok)) \
                    and not re.search(r"[*<>{}\s]", tok) and not tok.startswith(("http", "python", "docker", "make", "~")):
                if ".." in tok:
                    continue   # intervalos como fase7/1..6
                bases = ("", "docs_fase7", "entrega")
                if not any(os.path.exists(os.path.join(b, tok.rstrip("/"))) for b in bases):
                    ruins.append((texto[:50], tok))
    for t, tok in ruins:
        registrar("ERRO", "checklist", f"item marcado [x] cita '{tok}', que nao existe ({t}...)")
    registrar("OK", "checklist", f"{feitos} itens feitos, {pendentes} pendentes")


def checar_entrega():
    base = os.path.join("entrega", "fase7")
    for pasta in sorted(os.listdir(base)):
        arqs = [f for d, _, fs in os.walk(os.path.join(base, pasta)) for f in fs if f != ".gitkeep"]
        nivel = "OK" if arqs else "AVISO"
        registrar(nivel, "entrega", f"entrega/fase7/{pasta}: {len(arqs)} arquivo(s)")
    for p in glob.glob(os.path.join(base, "**", "LINK.txt"), recursive=True):
        ok = re.search(r"https?://", ler(p))
        registrar("OK" if ok else "AVISO", "entrega", f"{p}: " + ("link preenchido" if ok else "link do video ainda nao colado"))
    ident = ler(os.path.join("entrega", "IDENTIFICACAO.md"))
    rms = re.findall(r"RM:?\s*\d+", ident)
    registrar("OK" if len(rms) >= 4 and "[PREENCHER]" not in ident else "ERRO", "equipe", f"identificacao com {len(rms)} integrantes")
    sem = [p for p in glob.glob("docs_fase7/0*.md") + glob.glob("docs_fase7/CHECKLIST*.md") if "Turma ESOA4" not in ler(p)]
    for p in sem:
        registrar("ERRO", "equipe", f"{p} sem cabecalho da equipe")
    if not sem:
        registrar("OK", "equipe", "documentos da Fase 7 com cabecalho da equipe")


def checar_devsecops():
    pasta = os.path.join("entrega", "fase7", "3_devsecops", "evidencias")
    arqs = sorted(glob.glob(os.path.join(pasta, "0[1-9]_*.txt")))
    if not arqs:
        registrar("AVISO", "devsecops", "sem evidencias: rode bash scripts/ci_local.sh")
        return
    falhas = [os.path.basename(a) for a in arqs if "RESULTADO: OK" not in ler(a)]
    for a in falhas:
        registrar("ERRO", "devsecops", f"evidencia com falha: {a}")
    if not falhas:
        registrar("OK", "devsecops", f"{len(arqs)} etapas do pipeline local, todas OK")


def main():
    comps, fluxos = checar_arquitetura()
    checar_sincronia(comps, fluxos)
    checar_video(comps)
    checar_checklist()
    checar_entrega()
    checar_devsecops()
    icone = {"OK": "✔", "AVISO": "⚠", "ERRO": "✖"}
    for nivel, grupo, msg in resultados:
        print(f"{icone[nivel]} {nivel:<5} [{grupo}] {msg}")
    n = {k: sum(1 for r in resultados if r[0] == k) for k in icone}
    print(f"\nResumo: {n['OK']} ok, {n['AVISO']} avisos (pendencias humanas), {n['ERRO']} erros")
    sys.exit(1 if n["ERRO"] else 0)


if __name__ == "__main__":
    main()

"""Resume as evidencias do pipeline local em entrega/fase7/3_devsecops/evidencias/00_resumo.txt."""
import os
import re
import glob

EV = os.path.join("entrega", "fase7", "3_devsecops", "evidencias")
DETALHE = {
    "03_ruff": r"(All checks passed!|Found \d+ errors?)",
    "04_pytest": r"(\d+ passed.*|\d+ failed.*)",
    "05_bandit": r"(No issues identified\.|Total issues \(by severity\):)",
    "06_pip_audit": r"(No known vulnerabilities found|Found \d+ known vulnerabilit.*)",
    "09_trivy": r"(agrosmart:local \(debian[^│]*│[^│]*│\s*\d+)",
}


def main():
    linhas = ["RESUMO DO PIPELINE DEVSECOPS LOCAL (scripts/ci_local.sh)", ""]
    for arq in sorted(glob.glob(os.path.join(EV, "0[1-9]_*.txt"))):
        texto = open(arq, encoding="utf-8").read()
        nome = os.path.basename(arq)[:-4]
        titulo = texto.splitlines()[0].lstrip("# ").split("  (")[0]
        ok = "RESULTADO: OK" in texto
        extra = ""
        if nome in DETALHE and (m := re.search(DETALHE[nome], texto)):
            extra = " · " + re.sub(r"\s+", " ", m.group(1)).strip()
        if nome == "04_pytest" and (m := re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+%)", texto)):
            extra += f" · cobertura {m.group(1)}"
        linhas.append(f"[{'OK   ' if ok else 'FALHA'}] {titulo}{extra}")
    linhas.append("")
    todas = all("RESULTADO: OK" in open(a, encoding="utf-8").read() for a in glob.glob(os.path.join(EV, "0[1-9]_*.txt")))
    linhas.append("PIPELINE LOCAL: TUDO OK" if todas else "PIPELINE LOCAL: HA ETAPAS COM FALHA")
    with open(os.path.join(EV, "00_resumo.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    print("\n".join(linhas))


if __name__ == "__main__":
    main()

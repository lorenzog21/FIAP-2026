#!/usr/bin/env bash
# Reproduz localmente a mesma sequencia do CI (.github/workflows/ci.yml), usando Docker.
# Cada etapa grava sua saida em entrega/fase7/3_devsecops/evidencias/.
set -u
cd "$(dirname "$0")/.."
EV=entrega/fase7/3_devsecops/evidencias
mkdir -p "$EV"
FALHAS=0

etapa() {  # etapa <nome> <arquivo> <comando...>
  local nome="$1" arq="$2"; shift 2
  echo "==> $nome"
  { echo "# $nome  ($(date '+%Y-%m-%d %H:%M:%S'))"; echo "# comando: $*"; echo; } > "$EV/$arq"
  if "$@" >> "$EV/$arq" 2>&1; then
    echo "    OK" ; echo; echo "RESULTADO: OK" >> "$EV/$arq"
  else
    echo "    FALHOU (ver $EV/$arq)"; echo; echo "RESULTADO: FALHA" >> "$EV/$arq"; FALHAS=$((FALHAS+1))
  fi
}

etapa "Build da imagem de runtime"  01_build_runtime.txt   docker build -t agrosmart:local .
etapa "Build do estagio de CI"      02_build_ci.txt        docker build --target ci -t agrosmart:ci .
etapa "Qualidade: ruff"             03_ruff.txt            docker run --rm agrosmart:ci ruff check .
etapa "Testes + cobertura (pytest)" 04_pytest.txt          docker run --rm agrosmart:ci pytest --cov=. --cov-report=term
etapa "SAST: bandit"                05_bandit.txt          docker run --rm agrosmart:ci bandit -r . -c pyproject.toml -ll
etapa "Dependencias: pip-audit"     06_pip_audit.txt       docker run --rm agrosmart:ci pip-audit -r requirements.txt

TMP=$(mktemp -d)
cp -R data "$TMP/data" && cp -R test "$TMP/test"
etapa "Smoke test: pipeline no container" 07_smoke_pipeline.txt \
  docker run --rm -v "$TMP/data:/app/data" -v "$TMP/test:/app/test:ro" agrosmart:local python appleAnalisys.py
etapa "Smoke test: status do pipeline"    08_smoke_status.txt \
  docker run --rm -v "$TMP/data:/app/data" agrosmart:local python scripts/status.py
rm -rf "$TMP"

etapa "Scan da imagem: trivy (HIGH/CRITICAL)" 09_trivy.txt \
  docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "$HOME/.cache/trivy:/root/.cache" \
  aquasec/trivy:latest image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 agrosmart:local

python3 scripts/resumo_ci.py > /dev/null 2>&1 || true
echo; [ "$FALHAS" -eq 0 ] && echo "PIPELINE LOCAL: TUDO OK" || echo "PIPELINE LOCAL: $FALHAS etapa(s) com falha"
exit "$FALHAS"

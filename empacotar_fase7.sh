#!/usr/bin/env bash
# Gera AgroSmart_Fase7.zip com a entrega final (codigo, docs, dados Gold e logs, evidencias, slides e videos).
# Roda antes: python docs_fase7/gerar_guia.py && python scripts/verificar_entrega.py
set -euo pipefail
cd "$(dirname "$0")"
SAIDA="AgroSmart_Fase7.zip"
rm -f "$SAIDA"
zip -r "$SAIDA" \
  README.md requirements.txt requirements-dev.txt pyproject.toml Makefile arquitetura.toml \
  Dockerfile docker-compose.yml .dockerignore .github \
  ingest.py appleAnalisys.py generate_insights.py processar_dados.py automacao.py dashboard.py \
  observabilidade.py analise_processo.py demo_alerta_ao_vivo.py pages simulacao scripts tests \
  docs_fase6 docs_fase7 entrega test \
  data/bronze data/silver data/gold data/logs data/analise \
  exemplos_ia_generativa.md diagrama_*.md diagrama_*.svg \
  -x "*.DS_Store" "*/__pycache__/*" "entrega/fase7/6_pitch/slides/preview/*.html"
echo "Gerado: $SAIDA ($(du -h "$SAIDA" | cut -f1))"
python3 scripts/verificar_entrega.py | tail -3 || true

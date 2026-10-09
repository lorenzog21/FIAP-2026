#!/usr/bin/env bash
# Gera AgroSmart_Fase6.zip com tudo que a entrega pede (codigo, docs, dados Gold,
# prints e link/arquivo do video), sem .venv, .git nem as ~2.000 imagens de treino.
set -euo pipefail
cd "$(dirname "$0")"
SAIDA="AgroSmart_Fase6.zip"
rm -f "$SAIDA"
zip -r "$SAIDA" \
  README.md requirements.txt \
  ingest.py appleAnalisys.py generate_insights.py processar_dados.py automacao.py dashboard.py \
  iot docs_fase6 entrega test \
  data/bronze data/silver data/gold \
  exemplos_ia_generativa.md diagrama_*.md diagrama_*.svg \
  -x "*.DS_Store" "*/__pycache__/*"
echo "Gerado: $SAIDA ($(du -h "$SAIDA" | cut -f1))"
echo "Confira se entrega/prints/ tem os prints e se entrega/LINK_VIDEO.txt existe."

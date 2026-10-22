# AgroSmart - imagem unica para pipeline, dashboard e agendador.
# Os dados (data/, test/) NAO entram na imagem: sao montados como volume.
#
#   docker build -t agrosmart:local .                 # runtime (padrao = ultimo estagio)
#   docker build --target ci -t agrosmart:ci .        # estagio com ferramentas de qualidade/seguranca

FROM python:3.12-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# --- estagio de CI: ruff, pytest, bandit, pip-audit + codigo completo
FROM base AS ci
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY . .

# --- estagio final (runtime): sem ferramentas de dev, usuario sem privilegios
FROM base AS runtime
RUN useradd --create-home --uid 1000 agro
COPY --chown=agro:agro *.py ./
COPY --chown=agro:agro simulacao ./simulacao
COPY --chown=agro:agro pages ./pages
COPY --chown=agro:agro scripts/status.py ./scripts/status.py
RUN mkdir -p data test && chown -R agro:agro /app
USER agro

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3).status == 200 else 1)"

CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]

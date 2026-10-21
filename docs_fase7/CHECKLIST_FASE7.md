# Checklist da Fase 7 — AgroSmart (entrega final)

> Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)

A Fase 7 do curso foi dividida em 7 etapas internas, feitas uma por vez. Legenda: `[x]` pronto · `[ ]` pendente · 🧑 depende do time (gravar vídeo, colar link, conferir no PowerPoint).

Guia com as 3 cores (avaliação · time · pode tirar): [`GUIA_DA_ENTREGA.html`](GUIA_DA_ENTREGA.html). Conferência automática: `python scripts/verificar_entrega.py`.

## Etapa 0 — Organização e rastreabilidade
- [x] Pasta de entrega reorganizada em `entrega/fase6` e `entrega/fase7`
- [x] Checklist da Fase 7 (este arquivo)
- [x] Guia da entrega em HTML com 3 cores, gerado por `docs_fase7/gerar_guia.py`
- [x] Versão de avaliação do guia sem blocos do time: `docs_fase7/exportar_guia_avaliacao.py`
- [x] Decisões tomadas: sem SonarCloud, mineração com `pandas`, slides em PowerPoint, dashboard só local
- [x] Projeto movido para fora do iCloud (`~/dev/AgroSmart/FIAP-2026`)

## Etapa 1 — Execução containerizada (requisitos 2 e 3)
- [x] `Dockerfile` em 3 estágios (base, ci, runtime), usuário sem root
- [x] `.dockerignore`
- [x] `docker-compose.yml` com `pipeline`, `dashboard`, `scheduler` e `alerta-ao-vivo`
- [x] `requirements.txt` com versões fixas e `requirements-dev.txt`
- [x] `appleAnalisys.py` usa o cache Silver sozinho quando não há imagens montadas
- [x] Evidência: `entrega/fase7/2_execucao/logs/docker_compose_up.log` e prints
- [x] Exemplo de entrada → saída em `docs_fase7/02_execucao.md`

## Etapa 2 — Monitoramento e execução automatizada (requisito 4)
- [x] Logging estruturado em JSON (`observabilidade.py`, horários em UTC)
- [x] `data/logs/execucoes.jsonl` com status, duração por etapa e contagens
- [x] Healthcheck do dashboard e do agendador (`scripts/status.py`)
- [x] Página "Saúde do sistema" (`pages/1_Saude_do_sistema.py`)
- [x] Agendamento pelo serviço `scheduler` do compose
- [x] Evidência: `entrega/fase7/4_monitoramento/` (prints, logs e clipe)
- [x] Texto: `docs_fase7/04_monitoramento.md`

## Etapa 3 — Pipeline DevSecOps (requisito 3)
- [x] Testes `pytest` (19) em `tests/`
- [x] `.github/workflows/ci.yml` (qualidade, segurança, container)
- [x] Qualidade de código com `ruff` (`pyproject.toml`)
- [x] Vulnerabilidades: `pip-audit`, `bandit` e `trivy`
- [x] Build da imagem e smoke test do pipeline no container (`scripts/ci_local.sh`)
- [x] Evidência: `entrega/fase7/3_devsecops/evidencias/00_resumo.txt` e logs de cada etapa
- [x] Texto: `docs_fase7/03_devsecops.md`
- [x] Achados corrigidos e documentados (MD5 no bandit, variável sem uso no ruff)
- [ ] Executar o `ci.yml` no GitHub Actions (hoje só a versão local foi executada)

## Etapa 4 — Mineração de processos (requisito 5)
- [x] Pipeline instrumentado: event log por etapa e por folha (`observabilidade.py`)
- [x] `data/logs/event_log_execucoes.csv` e `data/logs/event_log_folhas.csv` com 39 execuções
- [x] `analise_processo.py`: grafo de fluxo, métricas, variantes e relatório
- [x] Diagramas do processo em `entrega/fase7/5_processo_e_video_final/analise/`
- [x] Análise escrita com gargalos, variações e melhorias: `docs_fase7/05_processo.md`
- [x] Melhoria aplicada e medida (predição por folha 3,7× mais rápida)

## Etapa 5 — Arquitetura final e documentação (requisitos 1 e 2)
- [x] `arquitetura.toml` como fonte única (15 componentes, 15 fluxos)
- [x] Diagrama final gerado: `docs_fase7/arquitetura_final.png`
- [x] `scripts/verificar_entrega.py` (rastreabilidade)
- [x] Descrição dos componentes e do fluxo: `docs_fase7/01_arquitetura_final.md`
- [x] Descrição do funcionamento e exemplo de entrada e saída: `docs_fase7/02_execucao.md`
- [x] Evidências de execução em `entrega/fase7/2_execucao/`

## Etapa 6 — Pitch como produto (requisito 6)
- [x] Slides: `entrega/fase7/6_pitch/slides/AgroSmart_Pitch.pptx` (9 slides, com notas)
- [x] Canvas de negócio da Fase 5 reaproveitado e marcado como hipótese
- [x] Roteiro do vídeo pitch: `docs_fase7/roteiro_pitch.md`
- [ ] 🧑 Conferir os slides no PowerPoint
- [ ] 🧑 Gravar o vídeo pitch (novo) e colar o link em `entrega/fase7/6_pitch/video/LINK.txt`

## Etapa 7 — Vídeo final e fechamento (requisito 5)
- [x] Roteiro do vídeo final com tempos: `docs_fase7/roteiro_video_final.md`
- [x] Clipes de apoio em `entrega/fase7/2_execucao/` e `entrega/fase7/4_monitoramento/`
- [x] `python scripts/verificar_entrega.py` sem erros
- [x] `empacotar_fase7.sh` pronto
- [ ] 🧑 Gravar o vídeo final (5 a 8 min) e colar o link em `entrega/fase7/5_processo_e_video_final/video/LINK.txt`
- [ ] 🧑 Abrir os links em janela anônima
- [ ] 🧑 Rodar `./empacotar_fase7.sh` e entregar o zip

## Riscos e limitações
- Dados de sensor e cenários por talhão são **simulados**; todo material diz isso.
- Cobertura de testes de 29%; o dashboard foi verificado só no navegador.
- Fases 1–4 do curso: os artefatos não estão neste repositório.

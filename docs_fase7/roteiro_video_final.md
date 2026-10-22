# Roteiro do vídeo final (Fase 7 · 5 a 8 minutos)

> Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)

**Meta: 7 min 00 s.** Gravação de tela com narração. Cada bloco cobre componentes do diagrama (`arquitetura.toml`); o `scripts/verificar_entrega.py` confere que todos foram citados aqui.

## Preparação (antes de gravar)
1. Projeto fora do iCloud (`~/dev/AgroSmart/FIAP-2026`), Docker Desktop aberto.
2. Mantenha o histórico em `data/logs` (não apague): é ele que alimenta a página Saúde do sistema e a análise de processo.
3. Abas prontas: (a) `docs_fase7/arquitetura_final.png`; (b) terminal na raiz do projeto; (c) navegador em http://localhost:8501; (d) `entrega/fase7/5_processo_e_video_final/analise/dfg_execucoes.png` e `dfg_folhas.png`.
4. Fechar notificações; 1080p; não mostrar histórico do terminal nem pastas pessoais.

## Blocos

| Bloco | Tempo | Dur. | Tela | O que falar e mostrar |
|---|---|---|---|---|
| Abertura | 0:00–0:20 | 20 s | Slide de capa | Nome do projeto, **turma ESOA4 e os quatro nomes**. "Esta é a entrega final: a plataforma funcionando, a arquitetura, o pipeline DevSecOps, o monitoramento e a análise do processo." |
| 1. Visão geral | 0:20–1:10 | 50 s | Dashboard (topo) | O AgroSmart acompanha macieiras contra a Podridão Negra. Junta **sensores simulados** e **imagens de folhas** e entrega **decisão por talhão**. Mostrar valor atual e média, decisão por talhão. Dizer que os dados de sensor são simulados. |
| 2. Arquitetura final | 1:10–2:20 | 70 s | `arquitetura_final.png` | Seguir as setas numeradas. **Fontes:** sensores simulados, simulador de talhões, imagens de folhas. **Ingestão:** Data Lake Bronze. **Processamento:** visão computacional com Random Forest e a preparação de dados. **Decisão:** motor de regras, IA generativa simulada e alerta ao vivo. **Visualização:** dashboard e a página Saúde do sistema. **Plataforma:** containers, pipeline DevSecOps, observabilidade e mineração de processos. Dizer que o diagrama e a documentação são gerados de um único arquivo, `arquitetura.toml`. |
| 3. Execução ponta a ponta | 2:20–3:30 | 70 s | Terminal e navegador | Rodar `docker compose up --build`. **Entrada:** simulador de sensores e imagens. **Processamento:** o pipeline limpa os dados e classifica as folhas. **Automação:** o motor de regras gera alertas, risco e decisão. **Saída:** dashboard. Em outro terminal, `docker compose --profile demo run --rm alerta-ao-vivo`: mostrar o alerta ao vivo de risco fúngico e de solo seco aparecendo no dashboard. |
| 4. DevSecOps | 3:30–4:20 | 50 s | Terminal | Rodar (ou mostrar o resultado de) `bash scripts/ci_local.sh`. Explicar as etapas: build, ruff, testes, bandit, pip-audit, execução em container e trivy na imagem. Mostrar o resumo `00_resumo.txt` e o **achado real**: o bandit apontou MD5 na primeira execução; foi corrigido com `usedforsecurity=False`. Dizer que a cobertura de testes é de 29%. |
| 5. Monitoramento | 4:20–5:10 | 50 s | Navegador e terminal | Página **Saúde do sistema**: estado operacional, duração por etapa, histórico e **logs** da aplicação. `python scripts/status.py` e `docker compose ps` com os containers *healthy*. Explicar o agendador (`--profile continuo`) e a **observabilidade**: todo evento vai para `data/logs`. |
| 6. Análise de processo | 5:10–6:30 | 80 s | `dfg_execucoes.png`, `dfg_folhas.png`, relatório | Explicar a **mineração de processos** a partir do **event log**. Mostrar o grafo: o gargalo da execução é a extração das imagens (63% do tempo); o da folha é `classificar_folha` (94%). Variantes: execução com cache é 3,6× mais rápida; 3% das folhas vão para ação prioritária. **Melhoria aplicada:** `n_jobs=1` na predição, que caiu de 46 ms para 13 ms por folha (3,7×). Dizer com franqueza que a execução completa não melhorou, porque o gargalo dela é outro. |
| Encerramento | 6:30–7:00 | 30 s | Slide final | O que está pronto e o que falta: dados de campo simulados, cobertura de testes de 29%, CI executado localmente. Próximos passos: sensores reais em um pomar-piloto. Agradecer. |

## Depois de gravar
- Conferir a duração (entre 5:00 e 8:00) e cortar pausas.
- Subir no YouTube como **não listado** ou no Drive com acesso "qualquer pessoa com o link"; abrir o link em janela anônima.
- Colar o link em `entrega/fase7/5_processo_e_video_final/video/LINK.txt`.

# Entrega 6 — Roteiro do vídeo de demonstração (3 a 5 minutos)

> **AgroSmart — Fase 6** · Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)

Meta: **4 min 15 s** (255 s) + 10 s de abertura/encerramento. Gravação de tela com narração.

## Preparação (antes de gravar)

1. `python appleAnalisys.py` — gera a camada Gold.
2. `streamlit run dashboard.py` aberto no navegador (zoom 90–100%), rolado até "Alertas ao vivo".
3. Abas prontas: (a) `docs_fase6/arquitetura_fase6.svg`; (b) terminal na pasta do projeto, pronto para o simulador; (d) dashboard.
4. Fechar notificações; 1080p; não mostrar caminhos pessoais nem histórico do terminal.

## Blocos

| Bloco | Tempo | Duração | Tela | Fala (sugestão) |
|---|---|---|---|---|
| Abertura | 0:00–0:05 | 5 s | Slide/título | Nome do projeto, **nomes dos integrantes e turma** |
| 1. Visão geral | 0:05–0:35 | 30 s | Dashboard (topo) | "O AgroSmart monitora macieiras contra a Podridão Negra. Junta sensores do ambiente e fotos de folhas e transforma isso em alertas e decisões por talhão." |
| 2. Arquitetura | 0:35–1:20 | 45 s | Diagrama | "Fontes de dados, ingestão no Data Lake, processamento, motor de decisão e dashboard. Cada caixa é um script. O fluxo vai dos sensores e das imagens até a decisão por talhão." Apontar cada caixa na ordem. |
| 3. Coleta na simulação | 1:20–2:20 | 60 s | Terminal e `stream_simulado.csv` | Rodar `python simulacao/simulador_sensores.py --stdout --ritmo 0.5`. "Os sensores são simulados em Python: temperatura, umidade do solo, umidade do ar e luminosidade, uma leitura a cada 2 segundos, no formato CSV de uma Serial. Aqui o solo seca e a umidade do ar sobe. Também simulamos 4 talhões com cenários diferentes: equilibrado, úmido e quente, seco e com chuva, com falhas de sensor propositais." Abrir `stream_simulado.csv` e mostrar `processar_dados.py` limpando o fluxo. |
| 4. Automação ao vivo | 2:20–3:20 | 60 s | Terminal + dashboard lado a lado | Rodar `python demo_alerta_ao_vivo.py` (ritmo 1 s). "A cada leitura, as regras são testadas. Aqui a umidade do ar subiu e a temperatura entrou na faixa: alerta de risco fúngico com a ação recomendada. Agora o solo caiu abaixo de 30%: alerta de irrigação." Mostrar os alertas aparecendo na seção "Alertas ao vivo" do dashboard. |
| 5. Dashboard | 3:20–4:20 | 60 s | Dashboard | "Valor atual e média de cada sensor; decisão por talhão; evolução temporal, com X nas leituras corrigidas; mapa de risco por hora; folhas de maior risco com foto e diagnóstico; alertas e recomendações." Usar o filtro de talhão (T3, solo seco). |
| Encerramento | 4:20–4:25 | 5 s | Dashboard | "Plataforma integrada, base para a Fase 7." |

## Depois de gravar

- Conferir a duração (entre 3:00 e 5:00); cortar pausas.
- Subir no YouTube como **não listado** ou no Drive com acesso "qualquer pessoa com o link"; abrir o link em janela anônima para testar.
- Colar o link em `entrega/fase6/LINK_VIDEO.txt`.

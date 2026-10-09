# Entrega 6 — Roteiro do vídeo de demonstração (3 a 5 min)

Meta: **4 min 30 s**. Gravação de tela com narração; uma pessoa por bloco se a equipe quiser dividir a fala.

## Preparação (antes de gravar)

1. `python appleAnalisys.py --usar-cache-silver` (ou sem a flag, se as imagens estiverem locais) — gera a camada Gold.
2. `streamlit run dashboard.py` e deixar aberto no navegador, zoom 90–100%.
3. Abas prontas: **(a)** `docs_fase6/arquitetura_fase6.svg`, **(b)** circuito do TinkerCad com a simulação parada, **(c)** terminal com o pipeline, **(d)** dashboard.
4. Fechar notificações; resolução 1080p.

## Cenas

| # | Tempo | Tela | Fala (sugestão) |
|---|---|---|---|
| 1 | 0:00–0:30 | Dashboard (visão geral) | "O AgroSmart monitora macieiras contra a Podridão Negra. Ele junta dois tipos de dado: sensores do ambiente e fotos das folhas, e transforma isso em alertas e decisões por talhão." |
| 2 | 0:30–1:15 | Diagrama de arquitetura | "Cinco camadas: fontes de dados, ingestão no Data Lake (Bronze), processamento (Silver), motor de decisão (Gold) e dashboard. Cada camada é um script: `ingest.py`, `appleAnalisys.py`, `processar_dados.py`, `automacao.py` e `dashboard.py`." Passar o mouse/apontar cada bloco. |
| 3 | 1:15–2:00 | TinkerCad: iniciar simulação, abrir Serial Monitor | "Aqui está a coleta: um Arduino com sensor de temperatura, umidade do solo, luminosidade e um potenciômetro que simula a umidade do ar, já que o TinkerCad não tem DHT. Mexo na umidade do solo, e o LED azul de irrigação acende. Giro o potenciômetro, e o LED vermelho de risco fúngico acende. Os dados saem em CSV na Serial." |
| 4 | 2:00–2:30 | Terminal: rodar o pipeline | "Para volume, o simulador em Python gera leituras no mesmo formato, em quatro talhões com cenários diferentes, com falhas de sensor propositais. Um comando roda tudo: ingestão, visão computacional, modelo, processamento e automação." Mostrar as linhas `[ingest]`, `[processamento]`, `[automacao]`. |
| 5 | 2:30–3:15 | Mostrar `alertas.json` e `acoes_talhao.json` (ou o trecho no VS Code) | "A automação é um motor de regras. Ele consolida horas seguidas de condição ruim em um único alerta, por exemplo risco fúngico no T2 quando o ar passa de 75% com temperatura entre 24 e 32 graus. Para as folhas, o risco combina 70% da lesão com 30% do ambiente. No fim, cada talhão recebe uma decisão." |
| 6 | 3:15–4:15 | Dashboard: KPIs, decisão por talhão, séries temporais (trocar de aba), heatmap, folhas de maior risco, tabela de alertas | "No topo, os indicadores e a decisão de cada talhão. Aqui a evolução dos sensores, com os pontos corrigidos marcados com X. O mapa de risco mostra que o T2 fica crítico o dia todo. Aqui as folhas de maior risco com a foto e o diagnóstico em linguagem natural. E aqui os alertas com a recomendação." Usar o filtro de talhão na lateral para mostrar o T3 (solo seco). |
| 7 | 4:15–4:30 | Dashboard / slide final | "O sistema está integrado de ponta a ponta e serve de base para a entrega final da Fase 7. Obrigado." |

## Dicas

- Ensaiar uma vez cronometrando; cortar a cena 4 se passar de 5 min.
- Não mostrar caminhos pessoais do computador nem o histórico do terminal.
- Publicar no YouTube como **não listado** ou no Drive com acesso "qualquer pessoa com o link", e testar o link em aba anônima.
- Nomes e papéis na narração: combinar quem fala em cada cena (sugestão: 1–2 pessoa A, 3 pessoa B, 4–5 pessoa C, 6–7 pessoa D).

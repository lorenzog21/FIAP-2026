# Entrega 2 — Coleta de dados do ambiente (simulação)

> **AgroSmart — Fase 6** · Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)

Os dados do ambiente vêm de **sensores simulados em Python**, sem hardware. Há dois geradores, com o mesmo schema:

| Gerador | Arquivo | Saída | Uso |
|---|---|---|---|
| Lotes por talhão | [`ingest.py`](../ingest.py) | `data/bronze/sensores/batch_<ts>/sensor_T1..T4.json` | 4 talhões × 40 leituras horárias, com cenários distintos e ~5% de falhas |
| Fluxo de leitura contínua | [`simulacao/simulador_sensores.py`](../simulacao/simulador_sensores.py) | `data/bronze/stream_sensores/stream_simulado.csv` | 60 leituras a cada 2 s, no formato que um datalogger enviaria pela Serial |

## Sensores simulados

| Grandeza | Sensor representado | Faixa plausível | Unidade | Campo |
|---|---|---|---|---|
| Temperatura | termistor/TMP36 | −10 a 50 | °C | `temperatura_c` |
| Umidade do solo | sensor capacitivo de solo | 0–100 | % | `umidade_solo_pct` |
| Umidade do ar | higrômetro (tipo DHT) | 0–100 | % | `umidade_ar_pct` |
| Luminosidade | fotoresistor (LDR), relativa | 0–100 | % | `luminosidade_pct` |

Leituras fora da faixa são marcadas com `flag_anomalia` na ingestão e corrigidas no processamento.

## Cenários por talhão (`ingest.py`)

| Talhão | Cenário | Objetivo |
|---|---|---|
| T1 | equilibrado | Referência sem alertas |
| T2 | úmido e quente | Dispara risco fúngico e solo encharcado |
| T3 | seco | Dispara solo seco (irrigação) |
| T4 | evento de chuva | Pico de umidade em uma janela de 12 h |

## Fluxo contínuo (`simulador_sensores.py`)

Em 2 minutos o solo seca de ~62% para ~18% e a umidade do ar sobe de 50% para 92%, com a temperatura a 30 °C. Isso dispara, nesta ordem, **risco fúngico** e **solo seco** no alerta ao vivo (`demo_alerta_ao_vivo.py`).

```bash
python simulacao/simulador_sensores.py                       # grava o CSV
python simulacao/simulador_sensores.py --stdout --ritmo 1    # imprime linha a linha, para a captura
```

### Exemplo de dados gerados

```csv
talhao_id,t_ms,umidade_solo_pct,temperatura_c,umidade_ar_pct,luminosidade_pct,irrigacao
T1,2000,61.5,22.1,48.6,25.3,0
T1,4000,60.9,22.2,48.9,22.8,0
```

Arquivo completo: [`stream_simulado.csv`](../data/bronze/stream_sensores/stream_simulado.csv). A coluna `irrigacao` vale 1 quando o solo está abaixo de 30%.

## Capturas

- [`simulacao_stream.png`](../entrega/fase6/prints/simulacao_stream.png): saída do `simulador_sensores.py --stdout`
- [`simulacao_alerta_ao_vivo.png`](../entrega/fase6/prints/simulacao_alerta_ao_vivo.png): `demo_alerta_ao_vivo.py` disparando os alertas
- [`pipeline_terminal.png`](../entrega/fase6/prints/pipeline_terminal.png): execução completa do pipeline

> As capturas de terminal são renderizações da saída real dos comandos, não prints da janela do terminal. Para o vídeo, rode os comandos ao vivo.

## Como o fluxo entra no pipeline

1. O simulador grava o CSV em `data/bronze/stream_sensores/`.
2. `processar_dados.py` lê o CSV, trata texto no lugar de número, célula vazia, duplicatas de `t_ms` e valores fora da faixa, e grava `data/silver/sensores_stream.csv`.
3. O dashboard exibe a amostra, e `demo_alerta_ao_vivo.py` aplica as regras linha a linha.

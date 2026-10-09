# Entregas 3, 4 e 5 — Processamento, automação e dashboard

## 3. Processamento e preparação dos dados

Código: [`processar_dados.py`](../processar_dados.py)

**Fluxo de dados**

```
data/bronze/sensores/batch_<ts>/sensor_T*.json
   -> carregar_sensores_bronze()   (concatena os 4 talhões)
   -> limpar_sensores()            (anômalo -> NaN -> interpolação; marca valor_imputado;
                                    deriva hora, periodo_dia e risco_ambiental 0-1)
   -> data/silver/sensores_limpos.csv
   -> data/gold/dataset_dashboard.csv, resumo_talhoes.csv

data/gold/results.json (saída do modelo)
   -> tabela_diagnosticos()
   -> data/gold/diagnosticos.csv
```

**Exemplo do dataset processado** (`data/gold/dataset_dashboard.csv`)

```csv
talhao_id,timestamp,umidade_solo_pct,temperatura_c,umidade_ar_pct,luminosidade_pct,flag_anomalia,valor_imputado,hora,periodo_dia,risco_ambiental
T1,2026-08-01 06:00:00,53.0,26.8,56.5,2.8,False,False,6,manha,0.35
T1,2026-08-01 07:00:00,56.5,26.9,66.6,15.9,False,False,7,manha,0.35
T1,2026-08-01 08:00:00,61.0,26.8,53.4,35.8,False,False,8,manha,0.35
```

Cada execução: 160 leituras (4 talhões × 40 h), 10 corrigidas.

## 4. Automação inteligente (motor de regras)

Código: [`automacao.py`](../automacao.py)

**Decisões automatizadas**

| Regra | Condição | Severidade | Ação recomendada |
|---|---|---|---|
| `RISCO_FUNGICO` | umidade do ar ≥ 75% e temp. 24–32 °C | alta se ar ≥ 85%, senão média | Intensificar monitoramento foliar; evitar aspersão |
| `SOLO_SECO` | umidade do solo < 30% | alta se < 20% | Acionar irrigação |
| `SOLO_ENCHARCADO` | umidade do solo > 80% | média | Suspender irrigação; verificar drenagem |
| `CALOR_EXTREMO` | temperatura > 35 °C | média | Avaliar sombreamento |
| Risco da folha | `0,7 × área infectada + 0,3 × risco ambiental` | baixo < 0,35 ≤ médio < 0,60 ≤ alto | Recomendação por faixa de severidade |

Horas consecutivas com a mesma condição viram **um** alerta (início, fim, duração). A prioridade do talhão é *alta* se houver folha de risco alto ou alerta de severidade alta; *média* se houver folha doente ou risco médio; *baixa* caso contrário. A decisão é montada a partir das causas reais do talhão.

**Exemplo de saída — alerta (`data/gold/alertas.json`)**

```json
{
  "talhao_id": "T2", "tipo": "RISCO_FUNGICO", "origem": "sensor",
  "inicio": "2026-08-01T06:00:00", "fim": "2026-08-01T18:00:00",
  "severidade": "alta", "leituras": 13,
  "descricao": "Condicao favoravel ao fungo (ar umido + temperatura 24-32C)",
  "recomendacao": "Intensificar monitoramento foliar e evitar irrigacao por aspersao."
}
```

**Exemplo de saída — decisão por talhão (`data/gold/acoes_talhao.json`)**

```json
{
  "talhao_id": "T2", "folhas_analisadas": 3, "folhas_com_black_rot": 1,
  "pior_nivel_risco": "medio", "alertas_sensor": 4,
  "causas": ["RISCO_FUNGICO", "SOLO_ENCHARCADO"], "prioridade": "alta",
  "decisao": "Remover as folhas afetadas e reavaliar em 48h. Intensificar monitoramento foliar e evitar irrigacao por aspersao. Suspender irrigacao e verificar drenagem."
}
```

**Exemplo — folha (`data/gold/risco_folhas.csv`):** `applerot7.JPG`, talhão T2, 9,09% de área infectada, ar 78%, 26,4 °C, solo 78% → índice 0,36, **risco médio**. Sem o ambiente seria 0,06; o contexto do talhão elevou o risco.

## 5. Dashboard analítico

Código: [`dashboard.py`](../dashboard.py) — `streamlit run dashboard.py`

| Indicador | Origem | O que responde |
|---|---|---|
| Leituras de sensor | `dataset_dashboard.csv` | Volume de dados coletados no filtro atual |
| Folhas analisadas / com Black Rot (%) | `risco_folhas.csv` | Prevalência da doença |
| Risco ambiental médio (0–1) | `risco_ambiental` | Quão favorável ao fungo está o ambiente |
| Alertas de severidade alta | `alertas.csv` | Quantos problemas exigem ação imediata |
| Decisão por talhão (prioridade + texto) | `acoes_talhao.json` | O que fazer em cada talhão |
| Séries temporais (4 abas, com limiares) | `dataset_dashboard.csv` | Evolução de temperatura, umidade do ar, umidade do solo e luminosidade; ✕ marca leitura corrigida |
| Mapa de calor risco × hora | `risco_ambiental` | Em que horários cada talhão fica crítico |
| Saudável × Black Rot por talhão | `risco_folhas.csv` | Onde a doença se concentra |
| Dispersão área infectada × índice de risco | `risco_folhas.csv` | Como o ambiente muda o risco para a mesma lesão |
| Folhas de maior risco (foto + texto gerado) | `insights.json` | Diagnóstico em linguagem natural |
| Alertas por tipo e tabela de recomendações | `alertas.csv` | Detalhe e recomendação de cada episódio |

Filtros na lateral: talhões e severidade dos alertas.

Prints a entregar em `entrega/prints/` (tirar com o dashboard aberto): `dashboard_topo.png` (KPIs + decisões), `dashboard_series.png` (séries + heatmap) e `dashboard_folhas_alertas.png` (folhas + alertas).

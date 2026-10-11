# Dicionário de dados e justificativa da lógica de decisão

> **AgroSmart — Fase 6** · Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)

## Dicionário do dataset processado (`data/gold/dataset_dashboard.csv`)

| Coluna | Tipo | Unidade | Descrição |
|---|---|---|---|
| `talhao_id` | texto | — | T1 a T4 |
| `timestamp` | datetime (ISO 8601) | — | Momento da leitura, lido com `pd.to_datetime` |
| `umidade_solo_pct` | número | % (0–100) | Umidade do solo |
| `temperatura_c` | número | °C (−10 a 50) | Temperatura ambiente |
| `umidade_ar_pct` | número | % (0–100) | Umidade relativa do ar |
| `luminosidade_pct` | número | % (0–100) | Luminosidade relativa (LDR) |
| `flag_anomalia` | booleano | — | Leitura original fora da faixa plausível |
| `valor_imputado` | booleano | — | Valor corrigido por interpolação no tempo, dentro do talhão |
| `hora` | inteiro | h (0–23) | Hora da leitura |
| `periodo_dia` | texto | — | madrugada, manhã, tarde ou noite |
| `risco_ambiental` | número | 0–1 | Índice de risco calculado (abaixo) |

**Tratamento:** formatos de data convertidos para datetime; valores ausentes, não numéricos e fora da faixa viram NaN e são interpolados (`valor_imputado = True`); duplicatas de tempo removidas no log serial.

**`risco_ambiental`** = soma limitada a 1 de: umidade do ar ≥ 75% (+0,40); temperatura de 24 a 32 °C (+0,35) ou acima de 32 °C (+0,10); umidade do solo ≥ 70% (+0,25).

## Por que regras e não só Machine Learning

- **Transparência:** o agrônomo precisa saber *por que* o sistema alertou; cada regra tem uma frase e uma ação.
- **Poucos dados rotulados:** não há histórico de "incidentes de campo" com rótulo para treinar um modelo de alertas; limiares agronômicos conhecidos (umidade ≥ 75% e 24–32 °C favorecem o fungo) são mais confiáveis do que um modelo ajustado a dados simulados.
- **Reaproveitamento:** a parte que *exige* aprendizado, a leitura da folha na imagem, já usa ML (Random Forest sobre % de área doente e circularidade). O motor de regras combina essa saída com os sensores.
- **Evolução:** com dados reais de campo, as regras podem virar rótulos para treinar um classificador na Fase 7.

## Lógica de decisão em linguagem clara

1. A cada leitura, o sistema testa 4 condições (risco fúngico, solo seco, solo encharcado, calor extremo).
2. Horas seguidas na mesma condição formam um único alerta; a severidade é a mais alta do período.
3. Para cada folha, o risco soma 70% do tamanho da lesão e 30% do ambiente do talhão: abaixo de 0,35 é baixo, até 0,60 é médio, acima é alto.
4. Cada talhão recebe uma prioridade (alta, média, baixa) e uma decisão montada a partir das causas reais.

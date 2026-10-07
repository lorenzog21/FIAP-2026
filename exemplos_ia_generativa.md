# Exemplos de saida da IA generativa simulada

Cada exemplo mostra o registro de entrada (saida do modelo de ML combinada
com o contexto de sensor do talhao, quando disponivel) e o texto gerado pela
camada de sintese de linguagem natural (`generate_insights.gerar_diagnostico`).

## Exemplo 1 -- applehealthy10.JPG

**Entrada (JSON):**
```json
{
  "image": "applehealthy10.JPG",
  "predicted_class": "Apple___healthy",
  "probabilities_ml": {
    "Apple___healthy": 0.75,
    "Apple___Black_rot": 0.25
  },
  "real_infected_area_percentage": 0.0,
  "sensor_context": {
    "talhao_id": "T3",
    "timestamp": "2026-08-01T12:00:00",
    "umidade_solo_pct": 31.3,
    "temperatura_c": 29.4,
    "umidade_ar_pct": 43.8,
    "luminosidade_pct": 98.0,
    "flag_anomalia": false
  }
}
```

**Texto gerado:**

> Nenhuma lesão característica de Podridão Negra foi detectada na área foliar analisada. O modelo tem 75% de confiança nesse diagnostico. Manter inspeção periódica e boas práticas de circulação de ar entre as plantas.

## Exemplo 2 -- applerot4.JPG

**Entrada (JSON):**
```json
{
  "image": "applerot4.JPG",
  "predicted_class": "Apple___Black_rot",
  "probabilities_ml": {
    "Apple___healthy": 0.135,
    "Apple___Black_rot": 0.865
  },
  "real_infected_area_percentage": 22.95,
  "sensor_context": {
    "talhao_id": "T1",
    "timestamp": "2026-08-02T18:00:00",
    "umidade_solo_pct": 60.1,
    "temperatura_c": 23.9,
    "umidade_ar_pct": 52.9,
    "luminosidade_pct": 0.0,
    "flag_anomalia": false
  }
}
```

**Texto gerado:**

> O modelo detectou padrões de coloração compatíveis com Podridão Negra na folha analisada. A lesão está avançando sobre 22.9% da área foliar, em estágio moderado, com confiança do modelo de 86%. As condicoes registradas no talhão T1 (temperatura 23.9°C, umidade do ar 53%, umidade do solo 60%) não indicam fator ambiental de risco adicional. Recomenda-se poda sanitária das partes afetadas e avaliação de fungicida preventivo à base de cobre.

## Exemplo 3 -- applerot9.JPG

**Entrada (JSON):**
```json
{
  "image": "applerot9.JPG",
  "predicted_class": "Apple___Black_rot",
  "probabilities_ml": {
    "Apple___healthy": 0.03,
    "Apple___Black_rot": 0.97
  },
  "real_infected_area_percentage": 0.87,
  "sensor_context": {
    "talhao_id": "T4",
    "timestamp": "2026-08-02T13:00:00",
    "umidade_solo_pct": 61.5,
    "temperatura_c": 22.3,
    "umidade_ar_pct": 64.3,
    "luminosidade_pct": 80.3,
    "flag_anomalia": false
  }
}
```

**Texto gerado:**

> O modelo detectou padrões de coloração compatíveis com Podridão Negra na folha analisada. A lesão está comprometendo cerca de 0.9% da área foliar, um estágio inicial, com confiança do modelo de 97%. As condicoes registradas no talhão T4 (temperatura 22.3°C, umidade do ar 64%, umidade do solo 62%) não indicam fator ambiental de risco adicional. Recomenda-se remover as folhas afetadas e monitorar a evolução nos próximos dias.

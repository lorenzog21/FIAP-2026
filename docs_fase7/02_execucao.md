# Execução da plataforma (Fase 7 · requisito 2)

> Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)

A plataforma roda de ponta a ponta com um único comando, em container, sem instalar nada além do Docker.

```bash
docker compose up --build              # pipeline (1x) + dashboard em http://localhost:8501
docker compose --profile continuo up   # + agendador que reexecuta o pipeline a cada INTERVALO_SEGUNDOS (padrão 300)
docker compose --profile demo run --rm alerta-ao-vivo   # alertas ao vivo
```

## O que acontece quando sobe

| Passo | Serviço | O que faz | Saída |
|---|---|---|---|
| 1 | `pipeline` | **Entrada:** simula as leituras de sensor dos 4 talhões e cataloga as imagens. **Processamento:** extrai atributos das folhas, treina e aplica o Random Forest, limpa os dados. **Automação:** alertas, risco e decisão por talhão | arquivos em `data/silver` e `data/gold`, logs em `data/logs` |
| 2 | `dashboard` | **Saída:** interface web com indicadores, séries, folhas, alertas e a página *Saúde do sistema* | http://localhost:8501 |
| 3 | `scheduler` (opcional) | Repete o pipeline com dados novos a cada ciclo, alternando execução completa e com cache | histórico em `data/logs/execucoes.jsonl` |

O `dashboard` só inicia depois de o `pipeline` terminar com sucesso (`service_completed_successfully`). Os dados (`data/`, `test/`) são montados como volume, então ficam fora da imagem.

## Exemplo de entrada e saída (dados reais de uma execução)

**Entrada 1 · leitura de sensor** (`data/bronze/sensores/batch_*/sensor_T2.json`):

```json
{"talhao_id": "T2", "timestamp": "2026-08-01T06:00:00", "umidade_solo_pct": 77.9, "temperatura_c": 30.7,
 "umidade_ar_pct": 88.9, "luminosidade_pct": 0.0, "flag_anomalia": false}
```

**Entrada 2 · imagem de folha** `test/applerot7.JPG`, catalogada em `metadados_imagens_*.csv`:

```csv
applerot7.JPG,test,T2,2026-08-01T11:00:00,camera_manual
```

**Saída 1 · classificação e risco da folha** (`data/gold/risco_folhas.csv`):

```csv
applerot7.JPG,T2,Apple___Black_rot,9.09,0.36,medio,"umidade do ar elevada (78%); temperatura na faixa favorável à proliferação fúngica (26.4°C); solo com alta retenção de umidade (78%)",Recomenda-se remover as folhas afetadas e monitorar a evolução nos próximos dias.
```

**Saída 2 · decisão do talhão** (`data/gold/acoes_talhao.json`):

```json
{"talhao_id": "T2", "folhas_com_black_rot": 1, "alertas_sensor": 4, "causas": ["RISCO_FUNGICO", "SOLO_ENCHARCADO"],
 "prioridade": "alta",
 "decisao": "Remover as folhas afetadas e reavaliar em 48 h. Intensificar monitoramento foliar e evitar irrigação por aspersão. Suspender irrigação e verificar drenagem."}
```

**Saída 3 · alerta** (`data/gold/alertas.csv`): `T2, RISCO_FUNGICO, alta, 06:00 a 18:00, "Condição favorável ao fungo (ar úmido + temperatura 24-32 °C)"`.

## Evidências

| Evidência | Onde |
|---|---|
| Log de `docker compose up`: containers, imagem, usuário sem root e saída do pipeline | `entrega/fase7/2_execucao/logs/docker_compose_up.log` |
| Imagem do log acima | `entrega/fase7/2_execucao/prints/docker_compose_up.png` |
| Dashboard servido pelo container (topo, séries, folhas, alertas) | `entrega/fase7/2_execucao/prints/dashboard_container_*.png` |
| Execuções da Fase 6 (simulação, alerta ao vivo) | `entrega/fase6/prints/` e `entrega/fase6/videos/` |

## Decisões de projeto
- **Imagem única** para pipeline, dashboard e agendador: menos coisas para manter.
- **Usuário `agro` (uid 1000), sem root** dentro do container.
- **Healthcheck** no dashboard (`/_stcore/health`) e no agendador (`scripts/status.py`).
- **Sem imagens de treino na imagem:** quando não há imagens montadas, o pipeline reaproveita automaticamente as features da camada Silver.

# Monitoramento e execução automatizada (Fase 7 · requisito 4)

> Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)

## O que é registrado

| Registro | Arquivo | Conteúdo |
|---|---|---|
| Log da aplicação | `data/logs/app.log` | 1 JSON por evento: horário (UTC), nível, `run_id`, mensagem, etapa, duração |
| Resumo de execução | `data/logs/execucoes.jsonl` | 1 linha por execução: status, duração, modo, versão do pipeline, tempo de cada etapa, nº de leituras, anomalias, alertas e folhas por nível de risco |
| Event log por etapa | `data/logs/event_log_execucoes.csv` | caso = execução; atividade, início, fim, duração, recurso, resultado |
| Event log por folha | `data/logs/event_log_folhas.csv` | caso = folha; um evento por passo (extrair, classificar, associar sensor, diagnosticar, calcular risco, desfecho) |

Todos os horários são gravados em **UTC com fuso explícito** (`+00:00`), para que o host e os containers não misturem fusos.

## Como acompanhar o sistema

| Onde olhar | O que mostra | Como acessar |
|---|---|---|
| **Página "Saúde do sistema"** | Estado (operacional, dados desatualizados ou falha), última execução, duração, taxa de sucesso, alertas, leituras anômalas, duração por execução, tempo por etapa, histórico e log. Atualiza sozinha a cada 10 s | http://localhost:8501 → menu lateral → *Saude do sistema* |
| **`python scripts/status.py`** | O mesmo estado em texto; sai com código 0 (operacional), 1 (atenção/falha) ou 2 (sem dados); `--json` e `--max-idade N` | terminal, ou `docker compose exec scheduler python scripts/status.py` |
| **`docker compose ps`** | Estado e `healthy` de cada container | terminal |
| **`docker compose logs -f scheduler`** | Saída de cada execução agendada | terminal |

## Execução automatizada
O serviço `scheduler` do `docker-compose.yml` reexecuta o pipeline a cada `INTERVALO_SEGUNDOS` com uma semente nova (dados diferentes) e alterna o modo completo e o com cache Silver. Ele tem `healthcheck`: o container fica `unhealthy` se a última execução falhou ou se passou de 3 intervalos + 60 s sem executar.

## Estados do indicador

| Estado | Condição |
|---|---|
| 🟢 Operacional | última execução com sucesso e dentro do limite de idade |
| 🟡 Dados desatualizados | última execução com sucesso, mas mais antiga que o limite (padrão 15 min na página) |
| 🔴 Falha | última execução terminou com erro |

## Evidências
- Prints da página *Saúde do sistema*, do terminal (`compose ps`, `status.py`, `app.log`) e um clipe do painel se atualizando: `entrega/fase7/4_monitoramento/`.
- Texto da evidência de terminal: `entrega/fase7/4_monitoramento/logs/monitoramento_evidencia.txt`.

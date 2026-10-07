# AgroSmart -- Fase 6 (plataforma integrada)

Documentação da Fase 6 em [`docs_fase6/`](docs_fase6/):
[arquitetura](docs_fase6/01_arquitetura.md) ·
[IoT / TinkerCad](docs_fase6/02_iot_tinkercad.md) ·
[processamento, automação e dashboard](docs_fase6/03_a_05_processamento_automacao_dashboard.md) ·
[roteiro do vídeo](docs_fase6/06_roteiro_video.md).

```bash
pip install -r requirements.txt
python appleAnalisys.py --usar-cache-silver   # sem a flag, relê todas as imagens
streamlit run dashboard.py
```

---

# AgroSmart -- Fase 5

Pipeline de diagnóstico de Podridão Negra (*Black Rot*) em folhas de maçã a
partir de imagem, enriquecido com dados simulados de sensor de talhão e uma
camada de síntese de linguagem natural ("IA generativa simulada").

## Mapa dos artefatos da entrega

| Requisito | Artefato |
|---|---|
| 1. Arquitetura de Dados com Data Lake | [diagrama_datalake.md](diagrama_datalake.md) (diagrama + explicação das camadas) |
| 2. Ingestão, administração e manutenção | [diagrama_ingestao.md](diagrama_ingestao.md) (fluxo + exemplo de dado ingerido + doc de manutenção) |
| 3. IA Generativa para apoio à decisão | [exemplos_ia_generativa.md](exemplos_ia_generativa.md) (saídas reais) + seção [IA generativa simulada](#ia-generativa-simulada) abaixo (funcionamento) |
| 4. Modelo de Negócio e Inteligência de Dados | Canvas + vídeo -- produzidos fora deste repositório (Canva/Miro/PowerPoint), não depende de código |

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python appleAnalisys.py
```

Um único comando (`python appleAnalisys.py`) executa o pipeline completo,
sem intervenção manual:

`ingestão (Bronze) -> extração de features (Silver) -> treino + predição ->
resultados enriquecidos (Gold) -> geração de insights em linguagem natural`

Ao final, a raiz do projeto ganha `exemplos_ia_generativa.md` com 3 exemplos
completos de entrada + texto gerado, prontos para colar na entrega.

> `results.json` na raiz é um artefato antigo, de uma versão anterior do
> script. O resultado atual e canônico do pipeline é `data/gold/results.json`.

## Camadas do Data Lake

**Bronze (bruta)** -- `data/Apple___healthy/`, `data/Apple___Black_rot/`,
`test/` e `data/bronze/`: armazena os dados exatamente como chegam -- as
imagens `.JPG` das folhas, sem nenhum processamento, mais os arquivos brutos
de sensor (`data/bronze/sensores/batch_<timestamp>/sensor_<talhao>.json`) e
o metadado que liga cada imagem a um talhão
(`data/bronze/metadados_imagens_<timestamp>.csv`). É o "estoque de
matéria-prima": nada aqui é confiável ainda, só preservado.

**Silver (confiável)** -- `data/silver/`: dados limpos, validados e
estruturados. É onde entram as features extraídas de cada imagem
(`area_doente_ratio`, `circularity`) em `features_treino.csv` e
`features_teste.csv`, já filtradas de erros de leitura -- imagem corrompida
é descartada e listada em `validation_log.txt` (mesma checagem `if img is
None` do código original).

**Gold (refinada)** -- `data/gold/`: dados prontos para consumo direto por
sistemas ou pessoas. `results.json` traz diagnóstico, probabilidade,
recomendação e o contexto de sensor do talhão para cada imagem de teste;
`insights.json` traz, para cada imagem, o texto de diagnóstico em linguagem
natural gerado pela camada de IA generativa simulada.

## Estratégia de manutenção e ingestão

- **Versionamento (append-only):** cada execução de `ingest.py` (chamada
  automaticamente por `appleAnalisys.py`) grava um novo lote carimbado com
  data/hora em `data/bronze/sensores/batch_<timestamp>/` e
  `data/bronze/metadados_imagens_<timestamp>.csv`. Nenhum lote anterior é
  sobrescrito. `data/bronze/LATEST_BATCH.txt` aponta para o lote mais
  recente, e `data/bronze/ingestion_log.jsonl` acumula um registro por
  execução (uma linha JSON por lote).
- **Validação:** imagem corrompida ou ilegível é descartada e logada
  (`data/silver/validation_log.txt`). Leitura de sensor fora de faixa
  plausível (ex.: umidade negativa ou acima de 100%) não é descartada --
  fica marcada com `flag_anomalia: true` e o motivo em `motivo_flag`, para
  auditoria, já que descartar silenciosamente uma leitura de sensor real
  esconderia falhas de hardware que a equipe de campo precisa saber que
  aconteceram.
- **Confiabilidade / completude:** cada lote de ingestão registra, em
  `ingestion_log.jsonl`, quantas leituras de sensor foram geradas por
  talhão, quantas foram flagadas, e quantas imagens foram catalogadas contra
  o total esperado -- permitindo detectar uma ingestão incompleta.

## IA generativa simulada

`generate_insights.py` substitui a antiga `statusLeaves()` (um `if/elif`
fixo por faixa de porcentagem). A nova função `gerar_diagnostico()` combina
múltiplas variáveis -- classe prevista, confiança do modelo, % de área
infectada e o contexto ambiental do talhão (umidade do ar, temperatura,
umidade do solo) -- calculando um índice de risco contínuo (não apenas uma
checagem de limiar único) e selecionando entre variações de fraseado. Não
chama nenhuma API paga: é um motor de templates parametrizados que simula o
comportamento de uma camada de geração de linguagem natural. Veja
`exemplos_ia_generativa.md` para os exemplos completos.

## Fontes de dados simuladas

- **Sensor de solo/clima:** 4 talhões (`T1`-`T4`), ~40 leituras horárias
  cada, campos `talhao_id`, `timestamp`, `umidade_solo_pct`,
  `temperatura_c`, `umidade_ar_pct`. ~5% das leituras simulam falha de
  sensor (valores fora de faixa) de propósito, para exercitar a validação.
- **Metadado de imagem:** liga cada imagem (treino e teste) a um talhão, uma
  data de captura e um equipamento (`drone` ou `camera_manual`), via
  atribuição determinística (hash do nome do arquivo) -- reprodutível entre
  execuções sem precisar persistir um mapeamento à parte.

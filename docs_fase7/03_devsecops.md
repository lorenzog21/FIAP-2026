# Pipeline DevSecOps (Fase 7 · requisito 3)

> Turma ESOA4 · Cayo Gonçalves de Morais Malara (RM 551243) · Igor Nunes Teixeira (RM 551099) · Lorenzo Guimarães (RM 99621) · Thiago Bullara Leite (RM 99461)

## Arquivos de configuração

| Arquivo | Função |
|---|---|
| `Dockerfile` | Imagem em 3 estágios: `base` (Python 3.12 + dependências), `ci` (ferramentas de qualidade e segurança) e `runtime` (usuário `agro`, sem root, sem ferramentas de dev) |
| `docker-compose.yml` | Serviços `pipeline`, `dashboard`, `scheduler` (perfil `continuo`) e `alerta-ao-vivo` (perfil `demo`) |
| `.github/workflows/ci.yml` | Pipeline para o GitHub Actions: 3 jobs (qualidade, segurança, container) |
| `scripts/ci_local.sh` | Mesma sequência do CI, rodando localmente com Docker, gravando evidências |
| `pyproject.toml` | Regras do ruff, do pytest e do bandit |
| `requirements.txt` / `requirements-dev.txt` | Dependências com versões fixas (runtime e desenvolvimento) |

## Etapas do pipeline

| # | Etapa | Ferramenta | O que garante | Resultado local |
|---|---|---|---|---|
| 1 | Build da imagem de runtime | `docker build` | a aplicação empacota | OK |
| 2 | Build do estágio de CI | `docker build --target ci` | ambiente de teste reproduzível (Python 3.12) | OK |
| 3 | **Qualidade de código** | `ruff` (regras E, F, W, B, UP) | estilo, variáveis sem uso, bugs comuns | sem achados |
| 4 | **Testes e cobertura** | `pytest --cov` | regras de decisão, limpeza de dados, observabilidade, simulador, análise de processo | 19 testes passando, cobertura 29% |
| 5 | **SAST** (análise estática de segurança) | `bandit` | padrões inseguros no código | sem achados de severidade média ou alta |
| 6 | **Vulnerabilidades em dependências** | `pip-audit` | CVEs conhecidos nas bibliotecas fixadas | nenhuma vulnerabilidade |
| 7 | **Execução em container** (smoke test) | `docker run` | o pipeline completo roda dentro da imagem final | OK |
| 8 | Status pós-execução | `scripts/status.py` | a execução foi registrada como `operacional` | OK |
| 9 | **Vulnerabilidades na imagem** | `trivy` (HIGH e CRITICAL, só com correção disponível) | sistema operacional e pacotes da imagem | 0 vulnerabilidades |

O `ci.yml` executa as mesmas etapas, com `needs`: o job de container só roda se qualidade e segurança passarem.

Como rodar: `bash scripts/ci_local.sh` (ou `make ci`). Cada etapa grava seu log em `entrega/fase7/3_devsecops/evidencias/` e o resumo em `00_resumo.txt`.

## O que o pipeline encontrou (e o que foi feito)

Na primeira execução, o pipeline **falhou** em 2 etapas, e isso é o comportamento esperado de um pipeline útil. Os logs dessa execução estão em `evidencias/primeira_execucao_com_achados/`.

| Etapa | Achado | Decisão |
|---|---|---|
| ruff | variável `inicio_fim` atribuída e não usada em `analise_processo.py` | removida |
| bandit (B324, severidade alta) | uso de MD5 em `ingest.py` e `generate_insights.py` | o MD5 só gera números determinísticos (sorteio por talhão e semente de texto), sem finalidade de segurança; corrigido com `usedforsecurity=False`, que torna a intenção explícita e não altera os resultados |

Antes disso, o ruff também apontou 63 ocorrências no código legado (pontos e vírgulas sobrando, variável chamada `l`, `zip` sem `strict`); todas foram corrigidas, não ignoradas.

O bandit ainda lista 3 itens de severidade **baixa** (fora do filtro `-ll` do pipeline); o uso de `random` para simulação é um deles e é intencional.

## Limitações assumidas
- **Cobertura de 29%:** os testes cobrem a lógica de decisão, a limpeza, a observabilidade e a análise; o dashboard e as páginas Streamlit não têm teste automatizado (foram verificados no navegador).
- **Análise de qualidade só com ruff.** SonarCloud não foi usado: exige conta e token externos e o ruff cobre o requisito de análise estática de qualidade.
- **`ci.yml` não foi executado no GitHub Actions** (esta entrega não publica o código nem dispara o CI na nuvem); o mesmo conjunto de etapas foi executado localmente com Docker, que é o que as evidências mostram.

## Evidências
- Resumo: `entrega/fase7/3_devsecops/evidencias/00_resumo.txt` e `00_resumo_pipeline.png`
- Log de cada etapa: `01_build_runtime.txt` … `09_trivy.txt`
- Primeira execução, com os achados: `primeira_execucao_com_achados/`

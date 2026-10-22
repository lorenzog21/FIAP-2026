"""Event log, resumo de execucao e status."""
import csv
import json

import pytest

import observabilidade as obs
from scripts import status


def test_execucao_grava_event_log_e_resumo(pasta_tmp):
    run = obs.Execucao(modo="completo", seed=1)
    with run.etapa("ingestao", "ingest.py") as e:
        e.registros = 10
    with obs.folha("a.JPG", "classificar_folha", "appleAnalisys.py", "T1") as ev:
        ev["resultado"] = "Apple___healthy"
    resumo = run.finalizar(status="sucesso", alertas_sensor=3)

    linhas = list(csv.DictReader(open(obs.EV_ETAPAS, encoding="utf-8")))
    assert linhas[0]["atividade"] == "ingestao" and linhas[0]["resultado"] == "ok" and linhas[0]["registros"] == "10"
    folhas = list(csv.DictReader(open(obs.EV_FOLHAS, encoding="utf-8")))
    assert folhas[0]["case_id"].endswith(":a.JPG") and folhas[0]["resultado"] == "Apple___healthy"
    gravado = json.loads(open(obs.EXECUCOES, encoding="utf-8").read().splitlines()[-1])
    assert gravado["status"] == "sucesso" and gravado["alertas_sensor"] == 3 and resumo["run_id"] == run.run_id
    assert obs.atual is None


def test_etapa_com_erro_registra_e_propaga(pasta_tmp):
    run = obs.Execucao()
    with pytest.raises(ValueError):
        with run.etapa("treino_modelo", "appleAnalisys.py"):
            raise ValueError("falhou")
    linha = list(csv.DictReader(open(obs.EV_ETAPAS, encoding="utf-8")))[0]
    assert linha["resultado"] == "erro" and "ValueError" in linha["observacao"]
    run.finalizar(status="falha")


def test_folha_sem_execucao_ativa_e_noop(pasta_tmp):
    assert obs.atual is None
    with obs.folha("x.JPG", "classificar_folha", "r") as ev:
        ev["resultado"] = "ok"
    assert not (pasta_tmp / "data").exists()


def test_status_estados(pasta_tmp):
    assert status.avaliar([])["codigo"] == 2
    ok = {"run_id": "r", "status": "sucesso", "fim": "2999-01-01T00:00:00", "duracao_s": 1.0}
    assert status.avaliar([ok], max_idade=60)["estado"] == "operacional"
    velho = {**ok, "fim": "2000-01-01T00:00:00"}
    assert status.avaliar([velho], max_idade=60)["estado"] == "desatualizado"
    assert status.avaliar([{**ok, "status": "falha"}])["estado"] == "falha"


def test_horarios_sao_utc_com_fuso_explicito(pasta_tmp):
    run = obs.Execucao()
    with run.etapa("ingestao", "ingest.py"):
        pass
    run.finalizar()
    linha = list(csv.DictReader(open(obs.EV_ETAPAS, encoding="utf-8")))[0]
    assert linha["inicio"].endswith("+00:00") and linha["fim"].endswith("+00:00")
    resumo = json.loads(open(obs.EXECUCOES, encoding="utf-8").read().splitlines()[-1])
    assert resumo["inicio"].endswith("+00:00") and resumo["versao"] == obs.VERSAO_PIPELINE


def test_status_aceita_registro_antigo_sem_fuso(pasta_tmp):
    antigo = {"run_id": "r", "status": "sucesso", "fim": "2000-01-01T00:00:00", "duracao_s": 1.0}
    assert status.avaliar([antigo], max_idade=60)["estado"] == "desatualizado"

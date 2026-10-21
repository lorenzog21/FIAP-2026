import os
import sys
import cv2
import csv
import json
import numpy as np
from os import listdir
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

import ingest
import generate_insights
import processar_dados
import automacao
import observabilidade


RANDOM_SEED = 0
LABEL2IDX = {
    "Apple___healthy": 0,
    "Apple___Black_rot": 1
}
SEPARATOR = '/'

SILVER_DIR = os.path.join("data", "silver")
GOLD_DIR = os.path.join("data", "gold")


def extrair_caracteristicas(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None, 0.0

    # Converte de BGR para HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Faixas de cores no formato HSV

    # Tons de verde (Folha saudável)
    lower_green = np.array([25, 40, 40])
    upper_green = np.array([90, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)

    # Tons de marrom/amarelo escuro (Folha doente)
    lower_brown = np.array([0, 20, 20])
    upper_brown = np.array([24, 255, 255])
    mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)

    # Contagem de pixels
    green_pixels = cv2.countNonZero(mask_green)
    brown_pixels = cv2.countNonZero(mask_brown)
    total_leaf_pixels = green_pixels + brown_pixels

    # Calcula a porcentagem real da área doente
    area_doente_ratio = 0.0

    if total_leaf_pixels > 0:
        area_doente_ratio = brown_pixels / total_leaf_pixels

    # Calcula a circularidade para achar as bordas faltando, e soma as duas máscaras para pegar o formato inteiro da folha
    mask_full_leaf = cv2.bitwise_or(mask_green, mask_brown)
    contours, _ = cv2.findContours(mask_full_leaf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    circularity = 0.0
    if contours:
        cnt = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)
        if perimeter > 0:
            circularity = (4 * np.pi * area) / (perimeter ** 2)

    features = [area_doente_ratio, circularity]
    return features, (area_doente_ratio * 100)


# Mensagens da análise.
def statusLeaves(area_percentage):
    if area_percentage <= 20:
        return {
            "range": "0% - 20%",
            "message": "Infecção inicial ou leve. A folha apresenta os primeiros sinais de manchas de Podridão Negra.",
            "recommendation": "Monitore a planta. Remova e descarte as folhas afetadas. Garanta boa circulação de ar ao redor da planta e evite molhar as folhas durante a rega."
        }
    elif area_percentage <= 40:
        return {
            "range": "21% - 40%",
            "message": "Infecção moderada. As lesões fúngicas estão se expandindo pela área foliar.",
            "recommendation": "Realize poda sanitária removendo folhas e galhos infectados. Considere a aplicação de um fungicida preventivo à base de cobre, seguindo orientação agronômica."
        }
    elif area_percentage <= 60:
        return {
            "range": "41% - 60%",
            "message": "Infecção severa. A capacidade fotossintética da folha está visivelmente comprometida.",
            "recommendation": "Intervenção química recomendada com fungicidas sistêmicos. Limpe bem o chão ao redor da árvore (esporos do fungo sobrevivem em folhas caídas no inverno)."
        }
    elif area_percentage <= 80:
        return {
            "range": "61% - 80%",
            "message": "Estado crítico. Risco alto de desfolha precoce e contaminação de frutos e galhos.",
            "recommendation": "Poda drástica das áreas afetadas. Inspecione o tronco e galhos maiores em busca de cancros (feridas escuras). Aplicação de fungicida de ação curativa é urgente."
        }
    else:
        return {
            "range": "81% - 100%",
            "message": "Necrose total ou irreversível. A folha perdeu sua função e atua apenas como vetor de transmissão.",
            "recommendation": "Remoção imediata da folha ou do galho inteiro. Queime ou descarte o material infectado longe da plantação (nunca faça compostagem com esse material). Avalie a saúde geral da árvore."
        }


def _seed():
    if "--seed" in sys.argv:
        return int(sys.argv[sys.argv.index("--seed") + 1])
    return 0


def main():
    os.makedirs(SILVER_DIR, exist_ok=True)
    os.makedirs(GOLD_DIR, exist_ok=True)

    seed = _seed()
    silver_treino_path = os.path.join(SILVER_DIR, "features_treino.csv")
    sem_imagens = not any(os.path.isdir(os.path.join("data", d)) for d in LABEL2IDX)
    usar_cache = ("--usar-cache-silver" in sys.argv or sem_imagens) and os.path.exists(silver_treino_path)
    run = observabilidade.Execucao(modo="cache_silver" if usar_cache else "completo", seed=seed)

    try:
        _executar(run, seed, usar_cache, sem_imagens, silver_treino_path)
    except Exception as erro:
        observabilidade.log("ERROR", "execucao falhou", erro=repr(erro))
        run.finalizar(status="falha", erro=repr(erro))
        raise


def _executar(run, seed, usar_cache, sem_imagens, silver_treino_path):
    print("Executando ingestão (camada Bronze)...")
    with run.etapa("ingestao", "ingest.py") as e:
        lote = ingest.run_ingestion(seed=seed)
        sensores_por_talhao = ingest.carregar_sensores(lote["sensor_dir"])
        metadados_por_imagem = ingest.carregar_metadados(lote["metadados_path"])
        leituras = [linha_ for ls in sensores_por_talhao.values() for linha_ in ls]
        e.registros = len(leituras)
        run.resumo["leituras_sensor"] = len(leituras)
        run.resumo["leituras_anomalas"] = sum(1 for linha_ in leituras if linha_["flag_anomalia"])

    X = []
    y = []
    silver_treino_rows = []
    descartadas_treino = []

    if usar_cache:
        # Reaproveita as features ja extraidas (Silver) em vez de reler ~2.000 imagens
        print("Reusando features de treino da camada Silver ("
              + ("sem imagens de treino no disco" if sem_imagens else "--usar-cache-silver") + ")...")
        with run.etapa("carregar_cache_silver", "appleAnalisys.py") as e:
            with open(silver_treino_path, encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    X.append([float(row["area_doente_ratio"]), float(row["circularity"])])
                    y.append(LABEL2IDX[row["classe"]])
                    meta = metadados_por_imagem.get(row["imagem_id"])
                    silver_treino_rows.append({
                        "imagem_id": row["imagem_id"],
                        "classe": row["classe"],
                        "talhao_id": meta["talhao_id"] if meta else None,
                        "area_doente_ratio": float(row["area_doente_ratio"]),
                        "circularity": float(row["circularity"]),
                    })
            e.registros = len(X)
    else:
        print("Extraindo atributos das imagens de treino...")
        with run.etapa("extracao_features", "appleAnalisys.py") as e:
            for d in listdir("data"):
                path = "data" + SEPARATOR + d + SEPARATOR
                if not os.path.isdir(path) or d not in LABEL2IDX:
                    continue

                for f in listdir(path):
                    if ".JPG" in f.upper():
                        features, _ = extrair_caracteristicas(path + f)
                        if features is None:
                            descartadas_treino.append(f)
                            continue
                        X.append(features)
                        y.append(LABEL2IDX[d])
                        meta = metadados_por_imagem.get(f)
                        silver_treino_rows.append({
                            "imagem_id": f,
                            "classe": d,
                            "talhao_id": meta["talhao_id"] if meta else None,
                            "area_doente_ratio": features[0],
                            "circularity": features[1],
                        })
            e.registros = len(X)
            e.observacao = f"{len(descartadas_treino)} imagens descartadas"

    X = np.array(X)
    y = np.array(y)

    with open(silver_treino_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["imagem_id", "classe", "talhao_id", "area_doente_ratio", "circularity"]
        )
        writer.writeheader()
        writer.writerows(silver_treino_rows)

    with open(os.path.join(SILVER_DIR, "validation_log.txt"), "w", encoding="utf-8") as f:
        f.write(f"Lote de ingestão: {lote['batch_ts']}\n")
        f.write(f"Imagens de treino validas: {len(silver_treino_rows)}\n")
        f.write(f"Imagens de treino descartadas (ilegiveis): {len(descartadas_treino)}\n")
        for nome in descartadas_treino:
            f.write(f"  - {nome}\n")

    print(f"{len(silver_treino_rows)} imagens válidas, {len(descartadas_treino)} descartadas (camada Silver).")

    print("Treinando o RandomForest...")
    with run.etapa("treino_modelo", "appleAnalisys.py") as e:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=.2, random_state=RANDOM_SEED, stratify=y
        )
        rf = RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=RANDOM_SEED, n_jobs=-1)
        rf.fit(X_train, y_train)
        # v1.1: a predicao e feita folha a folha; com n_jobs=-1 cada chamada criava um pool de threads
        # (~45 ms por folha, 96% do tempo por folha segundo a analise de processo). Treino segue paralelo.
        rf.set_params(n_jobs=1)
        e.registros = len(X_train)
        run.resumo["acuracia_validacao"] = round(float(rf.score(X_test, y_test)), 4)

    # Gerando JSON.
    print("Analisando imagens de teste e gerando JSON (camada Gold)...")
    results = []
    silver_teste_rows = []
    IDX2LABEL = {v: k for k, v in LABEL2IDX.items()}

    with run.etapa("predicao_teste", "appleAnalisys.py") as etapa_pred:
      for d in listdir("test"):
        path = "test" + SEPARATOR + d
        if ".JPG" in path.upper():
            meta = metadados_por_imagem.get(d)
            talhao = meta["talhao_id"] if meta else None
            with observabilidade.folha(d, "extrair_atributos", "appleAnalisys.py", talhao) as ev:
                features, real_infected_percentage = extrair_caracteristicas(path)
                if features is None:
                    ev["resultado"] = "ilegivel"

            if features is None:
                print(f"Erro ao ler a imagem {path}. Pulando.")
                continue

            silver_teste_rows.append({
                "imagem_id": d,
                "area_doente_ratio": features[0],
                "circularity": features[1],
            })

            with observabilidade.folha(d, "classificar_folha", "appleAnalisys.py", talhao) as ev:
                x_input = np.array([features])
                probabilities = rf.predict_proba(x_input)[0]
                predicted_class = rf.predict(x_input)[0]
                ev["resultado"] = IDX2LABEL[predicted_class]

            if predicted_class == LABEL2IDX["Apple___healthy"]:
                area_to_report = 0.0
            else:
                area_to_report = round(real_infected_percentage, 2)

            status = statusLeaves(area_to_report)

            sensor_contexto = None
            with observabilidade.folha(d, "associar_sensor", "ingest.py", talhao) as ev:
                if meta:
                    leituras_talhao = sensores_por_talhao.get(meta["talhao_id"], [])
                    leitura = ingest.sensor_mais_proximo(leituras_talhao, meta["data_captura"])
                    if leitura:
                        sensor_contexto = {
                            "talhao_id": meta["talhao_id"],
                            "timestamp": leitura["timestamp"],
                            "umidade_solo_pct": leitura["umidade_solo_pct"],
                            "temperatura_c": leitura["temperatura_c"],
                            "umidade_ar_pct": leitura["umidade_ar_pct"],
                            "luminosidade_pct": leitura.get("luminosidade_pct"),
                            "flag_anomalia": leitura["flag_anomalia"],
                        }
                        ev["resultado"] = "leitura_anomala" if leitura["flag_anomalia"] else "ok"
                    else:
                        ev["resultado"] = "sem_leitura"
                else:
                    ev["resultado"] = "sem_metadado"

            results.append({
                "image": d,
                "predicted_class": IDX2LABEL[predicted_class],
                "probabilities_ml": {
                    IDX2LABEL[i]: round(float(prob), 6)
                    for i, prob in enumerate(probabilities)
                },
                "analysis_infected_area": {
                    "real_infected_area_percentage": area_to_report,
                    "diagnosis_case": status
                },
                "metadata": meta,
                "sensor_context": sensor_contexto,
            })
      etapa_pred.registros = len(results)

    silver_teste_path = os.path.join(SILVER_DIR, "features_teste.csv")
    with open(silver_teste_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["imagem_id", "area_doente_ratio", "circularity"])
        writer.writeheader()
        writer.writerows(silver_teste_rows)

    gold_results_path = os.path.join(GOLD_DIR, "results.json")
    with open(gold_results_path, "w", encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"Salvou {len(results)} predições em {gold_results_path} (camada Gold)")
    run.resumo["folhas_analisadas"] = len(results)
    run.resumo["folhas_com_black_rot"] = sum(1 for r in results if r["predicted_class"] == "Apple___Black_rot")

    print("Gerando insights com IA generativa simulada...")
    with run.etapa("geracao_insights", "generate_insights.py") as e:
        insights = generate_insights.gerar_insights(gold_results_path)
        e.registros = len(insights)

    print("Processando dados para analise (Fase 6)...")
    with run.etapa("processamento_dados", "processar_dados.py") as e:
        limpo, _ = processar_dados.processar(lote["sensor_dir"], gold_results_path)
        e.registros = len(limpo)
        run.resumo["leituras_corrigidas"] = int(limpo["valor_imputado"].sum())

    print("Executando automacao inteligente (motor de regras)...")
    with run.etapa("automacao_regras", "automacao.py") as e:
        alertas, risco, acoes = automacao.executar()
        e.registros = len(alertas)
        run.resumo["alertas_sensor"] = len(alertas)
        run.resumo["alertas_severidade_alta"] = sum(1 for a in alertas if a["severidade"] == "alta")
        run.resumo["folhas_risco_medio"] = int((risco["nivel_risco"] == "medio").sum())
        run.resumo["folhas_risco_alto"] = int((risco["nivel_risco"] == "alto").sum())
        run.resumo["talhoes_prioridade_alta"] = sum(1 for a in acoes if a["prioridade"] == "alta")

    run.finalizar(status="sucesso")


if __name__ == "__main__":
    main()

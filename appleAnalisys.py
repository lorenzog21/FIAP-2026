import os;
import cv2;
import json;
import numpy as np;
from os import listdir;
from sklearn.model_selection import train_test_split;
from sklearn.ensemble import RandomForestClassifier;

RANDOM_SEED = 0;
LABEL2IDX = {
    "Apple___healthy": 0,
    "Apple___Black_rot": 1
};
SEPARATOR = '/';

def extrair_caracteristicas(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return None, 0.0;

    # Converte de BGR para HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV);

    # Faixas de cores no formato HSV

    # Tons de verde (Folha saudável)
    lower_green = np.array([25, 40, 40]);
    upper_green = np.array([90, 255, 255]);
    mask_green = cv2.inRange(hsv, lower_green, upper_green);

    # Tons de marrom/amarelo escuro (Folha doente)
    lower_brown = np.array([0, 20, 20]);
    upper_brown = np.array([24, 255, 255]);
    mask_brown = cv2.inRange(hsv, lower_brown, upper_brown);

    # Contagem de pixels
    green_pixels = cv2.countNonZero(mask_green);
    brown_pixels = cv2.countNonZero(mask_brown);
    total_leaf_pixels = green_pixels + brown_pixels;

    # Calcula a porcentagem real da área doente
    area_doente_ratio = 0.0;
    
    if total_leaf_pixels > 0:
        area_doente_ratio = brown_pixels / total_leaf_pixels;

    # Calcula a circularidade para achar as bordas faltando, e soma as duas máscaras para pegar o formato inteiro da folha
    mask_full_leaf = cv2.bitwise_or(mask_green, mask_brown);
    contours, _ = cv2.findContours(mask_full_leaf, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE);
    
    circularity = 0.0
    if contours:
        cnt = max(contours, key=cv2.contourArea);
        area = cv2.contourArea(cnt);
        perimeter = cv2.arcLength(cnt, True);
        if perimeter > 0:
            circularity = (4 * np.pi * area) / (perimeter ** 2);

    features = [area_doente_ratio, circularity];
    return features, (area_doente_ratio * 100);

print("Extraindo atributos das imagens de treino...");
X = [];
y = [];

for d in listdir("data"):
    path = "data" + SEPARATOR + d + SEPARATOR
    if not os.path.isdir(path): continue
    
    for f in listdir(path):
        if ".JPG" in f.upper():
            features, _ = extrair_caracteristicas(path + f);
            if features is not None:
                X.append(features);
                y.append(LABEL2IDX[d]);

X = np.array(X);
y = np.array(y);

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, random_state=RANDOM_SEED, stratify=y);

print("Treinando o RandomForest...");
rf = RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=RANDOM_SEED, n_jobs=-1);
rf.fit(X_train, y_train);

# Mensagens da análise.
def statusLeaves(area_percentage):
    if area_percentage <= 20:
        return {
            "range": "0% - 20%",
            "message": "Infecção inicial ou leve. A folha apresenta os primeiros sinais de manchas de Podridão Negra.",
            "recommendation": "Monitore a planta. Remova e descarte as folhas afetadas. Garanta boa circulação de ar ao redor da planta e evite molhar as folhas durante a rega."
        };
    elif area_percentage <= 40:
        return {
            "range": "21% - 40%",
            "message": "Infecção moderada. As lesões fúngicas estão se expandindo pela área foliar.",
            "recommendation": "Realize poda sanitária removendo folhas e galhos infectados. Considere a aplicação de um fungicida preventivo à base de cobre, seguindo orientação agronômica."
        };
    elif area_percentage <= 60:
        return {
            "range": "41% - 60%",
            "message": "Infecção severa. A capacidade fotossintética da folha está visivelmente comprometida.",
            "recommendation": "Intervenção química recomendada com fungicidas sistêmicos. Limpe bem o chão ao redor da árvore (esporos do fungo sobrevivem em folhas caídas no inverno)."
        };
    elif area_percentage <= 80:
        return {
            "range": "61% - 80%",
            "message": "Estado crítico. Risco alto de desfolha precoce e contaminação de frutos e galhos.",
            "recommendation": "Poda drástica das áreas afetadas. Inspecione o tronco e galhos maiores em busca de cancros (feridas escuras). Aplicação de fungicida de ação curativa é urgente."
        };
    else:
        return {
            "range": "81% - 100%",
            "message": "Necrose total ou irreversível. A folha perdeu sua função e atua apenas como vetor de transmissão.",
            "recommendation": "Remoção imediata da folha ou do galho inteiro. Queime ou descarte o material infectado longe da plantação (nunca faça compostagem com esse material). Avalie a saúde geral da árvore."
        };

# Gerando JSON.
print("Analisando imagens de teste e gerando JSON...");
results = [];
IDX2LABEL = {v: k for k, v in LABEL2IDX.items()}

for d in listdir("test"):
    path = "test" + SEPARATOR + d
    if ".JPG" in path.upper():
        features, real_infected_percentage = extrair_caracteristicas(path)
        
        if features is None:
            print(f"Erro ao ler a imagem {path}. Pulando.")
            continue
            
        x_input = np.array([features])
        
        probabilities = rf.predict_proba(x_input)[0]
        predicted_class = rf.predict(x_input)[0]
        
        if predicted_class == LABEL2IDX["Apple___healthy"]:
            area_to_report = 0.0
        else:
            area_to_report = round(real_infected_percentage, 2)
            
        status = statusLeaves(area_to_report)
        
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
            }
        })

output_path = "results.json";

with open(output_path, "w", encoding='utf-8') as f:
    json.dump(results, f, indent=4, ensure_ascii=False);

print(f"Salvou {len(results)} predições no arquivo {output_path}");
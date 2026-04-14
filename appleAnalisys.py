import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from os import listdir
import cv2
import os

RANDOM_SEED = 0
IMG_SIZE = (256, 256)
LABEL2IDX = {
    "Apple___healthy": 0,
    "Apple___Black_rot": 1
    }


SEPARATOR = '/'


X = []
y = []

for d in listdir("data"):
    path = "data"+SEPARATOR+d+SEPARATOR
    if not os.path.isdir(path):
        continue
    imagesize = None
    for f in listdir(path):
        if ".JPG" in f:
            x = cv2.imread(path+f, cv2.IMREAD_GRAYSCALE) # read the image as grayscale
            currentSize = x.shape
            if imagesize is None:
                imagesize = currentSize
                print(f"imsize = {imagesize}, for {d}")
            elif imagesize != currentSize:
                print(f"Image {f} has size {currentSize} but expected {imagesize}. Skipping.")
                continue
            x = x.reshape(256*256,) # reshape to flatten the 256x256 pixel-matrix to a 1d array
            X.append(x)
            y.append(LABEL2IDX[d])


X = np.array(X)
y = np.array(y)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=.2, random_state=RANDOM_SEED, stratify=y)

ss = StandardScaler()
X_train = ss.fit_transform(X_train)
X_test = ss.transform(X_test)

from sklearn.ensemble import RandomForestClassifier
from sklearn.decomposition import PCA

# Reduce dimensions (reuse pca from above if already run, otherwise fit again)
pca_rf = PCA(n_components=100, random_state=RANDOM_SEED)
X_train_pca_rf = pca_rf.fit_transform(X_train)
X_test_pca_rf = pca_rf.transform(X_test)

# Train Random Forest
rf = RandomForestClassifier(n_estimators=200,
                             class_weight='balanced',
                             random_state=RANDOM_SEED,
                             n_jobs=-1)  # uses all CPU cores
rf.fit(X_train_pca_rf, y_train)

#rf.predict(X_input) -> for d in set 
#   name = 1  
#   prediction - heqlth or black Rot 
#   name +=

import json
import os

results = []

for d in listdir("test"):
    path = "test" + SEPARATOR + d
    if ".JPG" in path:
        x = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        x = x.reshape(256*256,)
        x = ss.transform([x])
        x_pca = pca_rf.transform(x)
        
        probabilities = rf.predict_proba(x_pca)[0]
        predicted_class = rf.predict(x_pca)[0]
        
        # Map index back to label name
        IDX2LABEL = {v: k for k, v in LABEL2IDX.items()}
        
        results.append({
            "image": d,
            "probabilities": {
                IDX2LABEL[i]: round(float(prob), 6)
                for i, prob in enumerate(probabilities)
            },
            "predicted_class": IDX2LABEL[predicted_class]
        })

# Save to JSON (creates if not exists, overwrites if exists)
output_path = "results.json"
with open(output_path, "w") as f:
    json.dump(results, f, indent=4)

print(f"Saved {len(results)} predictions to {output_path}")


from sklearn.ensemble import IsolationForest
import numpy as np

FEATURE_ORDER = [
    "pm25",
    "pm10",
    "no2",
    "co",
]

MIN_HISTORY_SIZE = 10

def detect_anomaly(history: list[list[float]], current: list[float]) -> tuple[bool, float]:
    if len(history) < MIN_HISTORY_SIZE:
        return False, 0.0

    data_matrix = np.array(history + [current])

    model = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_estimators=100
    )
    model.fit(data_matrix)

    prediction = model.predict([current])[0]
    score = model.decision_function([current])[0]

    anomaly = bool(prediction == -1)
    return anomaly, float(score)

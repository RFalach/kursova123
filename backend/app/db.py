from pymongo import MongoClient
from datetime import datetime
from typing import Optional

MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "air_quality"

_client: Optional[MongoClient] = None
_db = None

def get_db():
    global _client, _db
    if _client is None:
        _client = MongoClient(MONGO_URI)
        _db = _client[DATABASE_NAME]
    return _db

def register_sensor(
    sensor_id: str,
    name: str,
    latitude: float,
    longitude: float,
    installed_at: datetime
) -> bool:
    db = get_db()
    sensors_col = db["sensors"]

    if sensors_col.find_one({"sensor_id": sensor_id}):
        return False

    doc = {
        "sensor_id": sensor_id,
        "name": name,
        "location": {
            "type": "Point",
            "coordinates": [longitude, latitude]
        },
        "installed_at": installed_at,
        "status": "active"
    }
    sensors_col.insert_one(doc)
    return True

def get_sensor_history(sensor_id: str, limit: int = 100) -> list[list[float]]:
    from app.anomaly import FEATURE_ORDER

    db = get_db()
    cursor = db["measurements"].find(
        {"sensor_id": sensor_id},
        {key: 1 for key in FEATURE_ORDER}
    ).sort("timestamp", -1).limit(limit)

    history = []
    for doc in cursor:
        vec = [doc.get(key) for key in FEATURE_ORDER]
        if all(v is not None for v in vec):
            history.append(vec)

    history.reverse()
    return history

def save_measurement(doc: dict) -> None:
    db = get_db()
    db["measurements"].insert_one(doc)

def get_all_sensors() -> list[dict]:
    db = get_db()
    return list(db["sensors"].find({}, {"_id": 0}))

def get_measurements(
    sensor_id: str,
    parameter: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = 500
) -> list[dict]:
    db = get_db()
    query = {"sensor_id": sensor_id}

    if from_date or to_date:
        query["timestamp"] = {}
        if from_date:
            query["timestamp"]["$gte"] = from_date
        if to_date:
            query["timestamp"]["$lte"] = to_date

    fields = {"_id": 0}
    if parameter:
        fields = {"_id": 0, "timestamp": 1, parameter: 1, "anomaly": 1, "anomaly_score": 1}

    cursor = db["measurements"].find(query, fields).sort("timestamp", -1).limit(limit)
    return list(cursor)

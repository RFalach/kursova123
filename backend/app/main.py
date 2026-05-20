from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uvicorn

from app.anomaly import detect_anomaly, FEATURE_ORDER
from app.db import (
    get_db, register_sensor, get_sensor_history, save_measurement,
    get_all_sensors, get_measurements
)

class SensorInfo(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float

class MeasurementValues(BaseModel):
    pm25: float
    pm10: float
    no2: float
    co: float

class IncomingData(BaseModel):
    sensor: SensorInfo
    timestamp: Optional[datetime] = None
    measurements: MeasurementValues

class SensorResponse(BaseModel):
    sensor_id: str
    name: str
    latitude: float
    longitude: float
    status: str
    installed_at: datetime

class MeasurementResponse(BaseModel):
    timestamp: datetime
    pm25: float | None = None
    pm10: float | None = None
    no2: float | None = None
    co: float | None = None
    anomaly: bool | None = None
    anomaly_score: float | None = None

app = FastAPI(
    title="Air Quality Monitor API",
    description="API для збору даних з IoT-сенсорів (через OpenAQ) "
                "та виявлення аномалій за допомогою Isolation Forest.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/data", summary="Прийняти дані від сенсора")
async def receive_data(payload: IncomingData):
    sensor = payload.sensor
    sensor_id = sensor.id
    timestamp = payload.timestamp or datetime.utcnow()

    register_sensor(
        sensor_id=sensor_id,
        name=sensor.name,
        latitude=sensor.latitude,
        longitude=sensor.longitude,
        installed_at=timestamp
    )

    m = payload.measurements
    meas_values = {
        "pm25": m.pm25,
        "pm10": m.pm10,
        "no2": m.no2,
        "co": m.co,
    }

    current_vector = [ m.pm25, m.pm10, m.no2, m.co ]

    history = get_sensor_history(sensor_id, limit=100)

    is_anomaly, score = detect_anomaly(history, current_vector)

    doc = {
        "sensor_id": sensor_id,
        "timestamp": timestamp,
        "pm25": m.pm25,
        "pm10": m.pm10,
        "no2": m.no2,
        "co": m.co,
        "anomaly": is_anomaly,
        "anomaly_score": score
    }

    save_measurement(doc)

    return {
        "status": "ok",
        "anomaly": is_anomaly
    }


@app.get("/api/sensors")
async def list_sensors():
    sensors = get_all_sensors()
    result = []
    for s in sensors:
        coords = s.get("location", {}).get("coordinates", [0, 0])
        result.append({
            "sensor_id": s["sensor_id"],
            "name": s["name"],
            "latitude": coords[1],
            "longitude": coords[0],
            "status": s.get("status", "active"),
            "installed_at": s.get("installed_at")
        })
    return result

@app.get("/api/measurements")
async def list_measurements(
    sensor_id: str,
    parameter: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = 500
):
    data = get_measurements(
        sensor_id=sensor_id,
        parameter=parameter,
        from_date=from_date,
        to_date=to_date,
        limit=limit
    )
    return data

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

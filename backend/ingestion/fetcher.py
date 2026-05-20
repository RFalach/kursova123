import time
import requests
from datetime import datetime, timezone

from ingestion.config import OPENAQ_API_KEY

SERVER_URL = "http://localhost:8000/api/data"
OPENAQ_BASE = "https://api.openaq.org/v3"

REQUIRED_PARAMETERS = ["pm25", "pm10", "no2", "co"]
TRACKED_LOCATION_IDS = [8087, 4401, 4767, 9773, 820326, 10665, 9320, 7728, 2623178, 2624491, 9307, 9773, 663501, 9589, 102]

REQUEST_DELAY = 2
CYCLE_PAUSE = 60 * 60

loc_meta = {}

def fetch_location_meta(location_id: int) -> dict | None:
    url = f"{OPENAQ_BASE}/locations/{location_id}"
    headers = {"X-API-Key": OPENAQ_API_KEY}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("results"):
            return None
        loc = data["results"][0]
        sensor_map = {}
        for s in loc.get("sensors", []):
            param = s["parameter"]["name"].lower()
            if param in REQUIRED_PARAMETERS:
                sensor_map[param] = s["id"]
        if len(sensor_map) != len(REQUIRED_PARAMETERS):
            return None

        return {
            "name": loc.get("name") or f"Location {location_id}",
            "lat": loc["coordinates"]["latitude"],
            "lon": loc["coordinates"]["longitude"],
            "sensor_map": sensor_map
        }
    except Exception:
        return None

def fetch_latest_measurements(location_id: int, sensor_map: dict) -> dict | None:
    url = f"{OPENAQ_BASE}/locations/{location_id}/latest"
    headers = {"X-API-Key": OPENAQ_API_KEY}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
    except Exception:
        return None

    values = {}
    for item in results:
        sid = item.get("sensorsId")
        if sid is None:
            continue

        for param, known_sid in sensor_map.items():
            if sid == known_sid:
                values[param] = float(item["value"])
                break

    if len(values) != len(REQUIRED_PARAMETERS):
        return None
    return values

def send_to_server(location_id: int, meta: dict, measurements: dict) -> bool:
    payload = {
        "sensor": {
            "id": f"openaq_{location_id}",
            "name": meta["name"],
            "latitude": meta["lat"],
            "longitude": meta["lon"]
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "measurements": measurements
    }
    try:
        resp = requests.post(SERVER_URL, json=payload, timeout=10)
        return resp.status_code == 200
    except requests.RequestException:
        return False

def run_cycle():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting cycle...")
    success = 0
    for loc_id in TRACKED_LOCATION_IDS:
        meta = loc_meta.get(loc_id)
        if not meta:
            print(f"  {loc_id}: FAIL (no metadata)")
            continue
        measurements = fetch_latest_measurements(loc_id, meta["sensor_map"])
        if measurements is None:
            print(f"  {loc_id}: FAIL (missing measurements)")
            continue
        if send_to_server(loc_id, meta, measurements):
            success += 1
            print(f"  {loc_id} ({meta['name'][:30]}): SUCCESS")
        else:
            print(f"  {loc_id} ({meta['name'][:30]}): FAIL (server error)")
        time.sleep(REQUEST_DELAY)
    print(f"Sent: {success}/{len(TRACKED_LOCATION_IDS)}")

if __name__ == "__main__":
    for loc_id in TRACKED_LOCATION_IDS:
        meta = fetch_location_meta(loc_id)
        if meta:
            loc_meta[loc_id] = meta
            print(f"  {loc_id}: {meta['name']}")
        else:
            print(f"  {loc_id}: FAILED - will be skipped")
        time.sleep(1)

    if not loc_meta:
        print("No valid locations. Exiting.")
        exit(1)

    try:
        while True:
            run_cycle()
            time.sleep(CYCLE_PAUSE)
    except KeyboardInterrupt:
        print("Stopped.")

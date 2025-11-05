import os
import requests
import json
from datetime import datetime, timedelta, timezone

# 🔧 Variables desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

# 🔐 Obtener token
token_url = f"{TENANT_URL}/v1.0/endpoint/default/token"
payload = {
    "grant_type": "client_credentials",
    "scope": "verify:events.read",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}
headers_token = {
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded"
}
resp = requests.post(token_url, data=payload, headers=headers_token)
resp.raise_for_status()
access_token = resp.json()["access_token"]

# 🔍 Obtener el evento más reciente
events_url = f"{TENANT_URL}/v1.0/events"
headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}
params_latest = {
    "event_type": '"authentication"',
    "size": 100,
    "sort_order": "desc"
}
resp = requests.get(events_url, headers=headers_api, params=params_latest)
resp.raise_for_status()
latest_data = resp.json()
latest_events = latest_data.get("events", [])

if not latest_events:
    print("⚠️ No se encontró ningún evento reciente.")
    exit()

latest_time = latest_events[0].get("time")
end_epoch = int(latest_time)
start_epoch = end_epoch - 3600000  # 1 hora en milisegundos

print("⏱️ Rango ajustado según el último evento:")
print("Inicio:", datetime.utcfromtimestamp(start_epoch / 1000))
print("Fin:", datetime.utcfromtimestamp(end_epoch / 1000))

# 🔍 Obtener eventos en ese rango
params_range = {
    "event_type": '"authentication"',
    "from": start_epoch,
    "to": end_epoch,
    "size": 100,
    "sort_order": "asc"
}
resp = requests.get(events_url, headers=headers_api, params=params_range)
resp.raise_for_status()
data = resp.json()
events = data.get("events", [])

print(f"\n🔍 Total eventos recibidos en la última hora: {len(events)}")
for i, e in enumerate(events):
    print(f"\n🔎 Evento {i+1}:")
    print(json.dumps(e, indent=2))

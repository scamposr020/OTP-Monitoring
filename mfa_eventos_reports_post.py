import os
import requests
import json
from datetime import datetime, timedelta, timezone

# 🔧 Variables desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

# 🕒 Rango de 1 hora (UTC) en milisegundos
now = datetime.now(timezone.utc)
end_dt = now.replace(minute=0, second=0, microsecond=0)
start_dt = end_dt - timedelta(hours=1)
start_epoch = int(start_dt.timestamp() * 1000)
end_epoch = int(end_dt.timestamp() * 1000)

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

# 🔍 Solicitud mínima al endpoint /events
events_url = f"{TENANT_URL}/v1.0/events"
headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}
params = {
    "event_type": '\\"authentication\\"',
    "from": start_epoch,
    "to": end_epoch,
    "size": 50,
    "sort_order": "asc"
}

resp = requests.get(events_url, headers=headers_api, params=params)
resp.raise_for_status()
data = resp.json()
events = data.get("events", [])

print(f"\n🔍 Total eventos recibidos: {len(events)}")
for i, e in enumerate(events[:3]):
    print(f"\n🔎 Evento {i+1}:")
    print(json.dumps(e, indent=2))

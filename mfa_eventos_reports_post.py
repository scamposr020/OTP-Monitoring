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

# 🕒 Rango de 5 horas de ayer (UTC): de 00:00 a 05:00
today = datetime.now(timezone.utc).date()
yesterday = today - timedelta(days=1)
start_dt = datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.utc)
end_dt = start_dt + timedelta(hours=5)
start_epoch = int(start_dt.timestamp() * 1000)
end_epoch = int(end_dt.timestamp() * 1000)

# 🔍 Consulta directa al endpoint /events con event_type y rango de tiempo
events_url = (
    f"{TENANT_URL}/v1.0/events?"
    f"event_type=\\\"authentication\\\""
)

headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

resp = requests.get(events_url, headers=headers_api)
resp.raise_for_status()
data = resp.json()

# 📤 Mostrar resumen y eventos
events = data.get("events", [])
print("\n⏱️ Rango de tiempo (UTC):")
print("Inicio:", start_dt)
print("Fin:", end_dt)
print(f"\n🔍 Total eventos recibidos: {len(events)}")

for i, e in enumerate(events):
    d = e.get("data", {})
    print(f"\n🔎 Evento {i+1}:")
    print(f"Usuario: {d.get('username')}")
    print(f"Resultado: {d.get('result')}")
    print(f"Método MFA: {d.get('mfamethod')}")
    print(f"Origen: {d.get('origin')}")
    print(f"Realm: {d.get('realm')}")
    print(f"Dispositivo: {d.get('mfadevice')}")
    print(f"Timestamp: {datetime.utcfromtimestamp(e.get('time') / 1000)}")

import os
import requests
import json

# 🔧 Variables desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

# 🔐 Obtener token
token_url = f"{TENANT_URL}/v1.0/endpoint/default/token"
payload = {
    "grant_type": "client_credentials",
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

# 🔍 Construir URL con filtros embebidos
events_url = (
    f"{TENANT_URL}/v1.0/events"
    "?event_type=\"authentication\""
    "&filter_key=data.result"
    "&size=1000"
    "&sort_order=desc"
)

headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

# 📥 Solicitud directa
resp = requests.get(events_url, headers=headers_api)
resp.raise_for_status()
data = resp.json()
events = data.get("events", [])

print(f"\n🔍 Total eventos recibidos: {len(events)}")
for i, e in enumerate(events[:3]):
    print(f"\n🔎 Evento {i+1}:")

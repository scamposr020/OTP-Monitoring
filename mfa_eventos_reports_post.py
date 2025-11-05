import os
import requests
import json
from datetime import datetime, timedelta, timezone

# 🔧 Variables desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

# 🕒 Rango de los últimos 7 días (UTC) en milisegundos
now = datetime.now(timezone.utc)
start_dt = now - timedelta(days=7)
start_epoch = int(start_dt.timestamp() * 1000)
end_epoch = int(now.timestamp() * 1000)

# 🔐 Obtener token
token_url = f"{TENANT_URL}/v1.0/endpoint/default/token"
payload = {
    "grant_type": "client_credentials",
    "scope": "verify:reports.read",
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

# 🔍 Llamada directa al endpoint /reports/mfa_activity
report_url = f"{TENANT_URL}/v1.0/reports/mfa_activity"
headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}
params = {
    "from": start_epoch,
    "to": end_epoch,
    "size": 100,
    "sort_order": "desc"
}

resp = requests.get(report_url, headers=headers_api, params=params)
resp.raise_for_status()
data = resp.json()
events = data.get("events", [])

print(f"\n🔍 Total eventos MFA recibidos: {len(events)}")
for i, e in enumerate(events):
    print(f"\n🔎 Evento {i+1}:")
    print(json.dumps(e, indent=2))

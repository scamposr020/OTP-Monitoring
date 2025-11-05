import os
import requests
import json
from datetime import datetime, timedelta, timezone

# 🔧 Variables desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# 🕒 Rango de 1 hora exacta (UTC) en milisegundos
now = datetime.now(timezone.utc)
end_dt = now.replace(minute=now.minute // 10 * 10, second=0, microsecond=0)
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

# 🔍 Inicializar paginación
events_url = f"{TENANT_URL}/v1.0/events"
headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}
params_base = {
    "from": start_epoch,
    "to": end_epoch,
    "size": 100,
    "sort_order": "asc"
}
all_events = []
max_pages = 5
page = 0
after_id = None
after_time = None

while page < max_pages:
    params = params_base.copy()
    if after_id and after_time:
        params["after_id"] = after_id
        params["after_time"] = after_time

    resp = requests.get(events_url, headers=headers_api, params=params)
    resp.raise_for_status()
    data = resp.json()
    events = data.get("events", [])

    if not events:
        print("⚠️ No se recibieron eventos en esta página.")
        break

    all_events.extend(events)
    print(f"📥 Página {page + 1}: {len(events)} eventos")

    # 🔎 Imprimir los primeros 5 eventos sin filtrar
    for i, e in enumerate(events[:5]):
        print(f"\n🔎 Evento {i+1} sin filtrar:")
        print(json.dumps(e, indent=2))

    last = events[-1]
    after_id = last.get("id")
    after_time = last.get("time")
    page += 1

print(f"\n🔍 Total eventos recibidos: {len(all_events)}")

import os
import requests
import json
from datetime import datetime, timedelta, timezone

# 🔧 Variables desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# 🕒 Definir rango de 1 hora exacta (UTC)
now = datetime.now(timezone.utc)
end_time = now.replace(minute=now.minute // 10 * 10, second=0, microsecond=0)
start_time = end_time - timedelta(hours=1)

# 🔐 Obtener token
token_url = f"{TENANT_URL}/v1.0/endpoint/default/token"
payload = {
    "grant_type": "client_credentials",
    "scope": "verify:audit.read",
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

# 🔍 Inicializar paginación por desplazamiento
search_url = f"{TENANT_URL}/v1.0/reports/mfa_activity"
headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}
all_hits = []
page = 0
size = 500
max_pages = 10

while page < max_pages:
    body = {
        "range_type": "time",
        "from": start_time.isoformat(),
        "to": end_time.isoformat(),
        "size": size,
        "from": page * size
    }

    resp = requests.post(search_url, headers=headers_api, json=body)
    resp.raise_for_status()
    data = resp.json()
    hits = data.get("response", {}).get("report", {}).get("hits", [])

    if not hits:
        break

    all_hits.extend(hits)
    print(f"📥 Página {page

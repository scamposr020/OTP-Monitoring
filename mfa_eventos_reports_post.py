import os
import requests
import json
from datetime import datetime, timedelta, timezone
import pprint

# 🔧 Variables desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# 🕒 Paso 1: Definir rango de 1 hora exacta (UTC)
now = datetime.now(timezone.utc)
end_time = now.replace(minute=now.minute // 10 * 10, second=0, microsecond=0)
start_time = end_time - timedelta(hours=1)

# 🔐 Paso 2: Obtener token
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
print("✅ Token obtenido")

# 🔍 Paso 3: Consultar eventos MFA en ese rango
search_url = f"{TENANT_URL}/v1.0/reports/mfa_activity"
headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}
body = {
    "range_type": "time",
    "from": start_time.isoformat(),
    "to": end_time.isoformat()
}
resp = requests.post(search_url, headers=headers_api, json=body)
resp.raise_for_status()
data = resp.json()

# 📄 Imprimir estructura completa del JSON recibido
pp = pprint.PrettyPrinter(indent=2, width=120)
print("📄 Estructura completa del JSON recibido:")
pp.pprint(data)

# 📋 Extraer eventos desde hits
hits = data.get("response

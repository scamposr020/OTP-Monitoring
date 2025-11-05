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

# 🔍 Consulta directa al endpoint /reports/mfa_activity
report_url = f"{TENANT_URL}/v1.0/reports/mfa_activity"

headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

resp = requests.get(report_url, headers=headers_api)
resp.raise_for_status()
data = resp.json()

# 📤 Mostrar todo el contenido recibido
print("\n🔍 Respuesta completa del endpoint /reports/mfa_activity:")
print(json.dumps(data, indent=2))

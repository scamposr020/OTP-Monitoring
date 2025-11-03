import os
import requests
import json
from datetime import datetime, timedelta, timezone
from openpyxl import Workbook

# 🔧 Variables desde entorno (GitHub Secrets)
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# 🔐 Paso 1: Obtener token
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

# 🕒 Paso 2: Consultar eventos MFA por POST en /reports/mfa_activity
since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
search_url = f"{TENANT_URL}/v1.0/reports/mfa_activity"
headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}
body = {
    "range_type": "time",
    "from": since
}
resp = requests.post(search_url, headers=headers_api, json=body)
resp.raise_for_status()
data = resp.json()

# 📋 Extraer eventos desde hits
hits = data.get("response", {}).get("report", {}).get("hits", [])
print(f"🔍 Se recibieron {len(hits)} eventos")

# 📦 Exportar a Excel
wb = Workbook()
ws = wb.active
ws.title = "Eventos MFA"
ws.append(["username", "result", "method", "timestamp", "device", "origin", "realm"])

resumen = []
for item in hits:
    src = item.get("_source", {})
    d = src.get("data", {})
    raw_time = src.get("time")
    readable_time = datetime.fromtimestamp(raw_time / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if raw_time else "N/A"

    ws.append([
        d.get("username"),
        d.get("result"),
        d.get("mfamethod"),
        readable_time,
        d.get("mfadevice"),
        d.get("origin"),
        d.get("realm")
    ])
    resumen.append(
        f"*Usuario:* {d.get('username')}\n"
        f"*Resultado:* {d.get('result')}\n"
        f"*Método:* {d.get('mfamethod')}\n"
        f"*Origen:* {d.get('origin')}\n"
        f"*Dispositivo:* {d.get('mfadevice')}\n"
        f"*Realm:* {d.get('realm')}\n"
        f"*Timestamp:* {readable_time}\n"
        "-----------------------------"
    )

output_file = "eventos_mfa.xlsx"
wb.save(output_file)
print(f"📂 Eventos exportados a {output_file}")

# 📤 Enviar resumen a Slack
if resumen:
    mensaje = {
        "text": f"🔐 *Eventos MFA recientes ({len(resumen)}):*\n" + "\n".join(resumen[:10])
    }
else:
    mensaje = {
        "text": "🔕 No se detectaron eventos MFA en la última hora."
    }

resp = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(mensaje), headers={"Content-Type": "application/json"})
if resp.status_code == 200:
    print("📤 Resumen enviado a Slack correctamente")
else:
    print(f"❌ Error al enviar a Slack: {resp.status_code}")
    print(resp.text)

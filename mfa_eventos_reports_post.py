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
    print(f"📥 Página {page + 1}: {len(hits)} eventos")
    if len(hits) < size:
        break

    page += 1

print(f"🔍 Total eventos recibidos: {len(all_hits)}")

# 📊 Contar eventos Email OTP
total_mfa = 0
success_count = 0
sent_count = 0
failure_count = 0
detalles = []

for item in all_hits:
    src = item.get("_source", {})
    d = src.get("data", {})
    method = d.get("mfamethod")
    result = d.get("result")
    raw_time = src.get("time")
    readable_time = datetime.fromtimestamp(raw_time / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if raw_time else "N/A"

    if method == "Email OTP":
        total_mfa += 1
        if result == "success":
            success_count += 1
        elif result == "sent":
            sent_count += 1
        elif result == "failure":
            failure_count += 1

    detalles.append(
        f"*Usuario:* {d.get('username')}\n"
        f"*Resultado:* {result}\n"
        f"*Método:* {method}\n"
        f"*Origen:* {d.get('origin')}\n"
        f"*Dispositivo:* {d.get('mfadevice')}\n"
        f"*Realm:* {d.get('realm')}\n"
        f"*Timestamp:* {readable_time}\n"
        "-----------------------------"
    )

# 📤 Enviar resumen completo a Slack
mensaje = {
    "text": (
        f"*Eventos MFA recientes ({total_mfa}) entre {start_time.strftime('%H:%M')} y {end_time.strftime('%H:%M')} UTC:*\n"
        f"• Email OTP - Success: {success_count}\n"
        f"• Email OTP - Sent: {sent_count}\n"
        f"• Email OTP - Failure: {failure_count}\n\n"
        + "\n".join(detalles)
    )
}

resp = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(mensaje), headers={"Content-Type": "application/json"})
if resp.status_code == 200:
    print("📤 Resumen enviado a Slack correctamente")
else:
    print(f"❌ Error al enviar a Slack: {resp.status_code}")
    print(resp.text)

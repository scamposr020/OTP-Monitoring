import os
import requests
from datetime import datetime, timedelta, timezone

# 🔧 Variables desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]  # debe estar configurado

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

# 🕒 Rango de hace 1 hora (UTC)
now = datetime.now(timezone.utc)
start_dt = now - timedelta(hours=1)
start_epoch = int(start_dt.timestamp() * 1000)
end_epoch = int(now.timestamp() * 1000)

# 🔍 Consulta al endpoint /events
events_url = (
    f"{TENANT_URL}/v1.0/events?"
    f"event_type=\\\"authentication\\\""
    f"&from={start_epoch}&to={end_epoch}"
    f"&size=700&sort_order=asc"
)
headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}
resp = requests.get(events_url, headers=headers_api)
resp.raise_for_status()
data = resp.json()

# 📊 Conteo de eventos
events = data.get("response", {}).get("events", {}).get("events", [])
total = len(events)
success = sum(1 for e in events if e.get("data", {}).get("result", "").lower() == "success")
failure = sum(1 for e in events if e.get("data", {}).get("result", "").lower() == "failure")
sent = sum(1 for e in events if e.get("data", {}).get("result", "").lower() == "sent")

# 📝 Formato del mensaje
summary = (
    f"*Resumen de eventos MFA (última hora UTC)*\n"
    f"🕒 Desde: {start_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
    f"🕒 Hasta: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
    f"🔍 Total eventos: *{total}*\n"
    f"✅ Success: *{success}*\n"
    f"❌ Failure: *{failure}*\n"
    f"📨 Sent: *{sent}*"
)

# 📤 Enviar a Slack
slack_payload = {"text": summary}
slack_resp = requests.post(SLACK_WEBHOOK_URL, json=slack_payload)
slack_resp.raise_for_status()

print("✅ Resumen enviado a Slack correctamente.")

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

# 🕒 Calcular rango de la última hora (UTC) en milisegundos
now = datetime.now(timezone.utc)
start_dt = now - timedelta(hours=1)
start_epoch = int(start_dt.timestamp() * 1000)
end_epoch = int(now.timestamp() * 1000)

# 🔍 Consulta directa al endpoint /events con event_type y rango de tiempo
events_url = (
    f"{TENANT_URL}/v1.0/events?"
    f"event_type=\\\"authentication\\\""
    f"&from={start_epoch}&to={end_epoch}"
    f"&size=100&sort_order=asc"
)

headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

resp = requests.get(events_url, headers=headers_api)
resp.raise_for_status()
data = resp.json()

# 📊 Filtrar eventos Email OTP y contar resultados
events = data.get("events", [])
email_otp_events = []
success_count = 0
sent_count = 0
failure_count = 0

for e in events:
    d = e.get("data", {})
    if d.get("mfamethod") == "Email OTP":
        email_otp_events.append(e)
        result = d.get("result")
        if result == "success":
            success_count += 1
        elif result == "sent":
            sent_count += 1
        elif result == "failure":
            failure_count += 1

# 📤 Mostrar resumen
print("\n⏱️ Rango de tiempo:")
print("Inicio:", datetime.utcfromtimestamp(start_epoch / 1000))
print("Fin:", datetime.utcfromtimestamp(end_epoch / 1000))
print(f"\n🔍 Total eventos Email OTP: {len(email_otp_events)}")
print(f"✅ Success: {success_count}")
print(f"📨 Sent: {sent_count}")
print(f"❌ Failure: {failure_count}")

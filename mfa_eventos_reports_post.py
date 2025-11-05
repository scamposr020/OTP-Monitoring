import os
import requests
import json
from datetime import datetime, timedelta, timezone

# 🔧 Variables desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# 🕒 Rango de 1 hora (UTC) en milisegundos
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
    "event_type": '\\"authentication\\"',
    "from": start_epoch,
    "to": end_epoch,
    "size": 100,
    "sort_order": "asc"
}
all_events = []
max_pages = 20
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

    last = events[-1]
    after_id = last.get("id")
    after_time = last.get("time")
    page += 1

print(f"\n🔍 Total eventos recibidos: {len(all_events)}")

# 📊 Filtrar y contar eventos MFA
total_mfa = 0
success_count = 0
sent_count = 0
failure_count = 0
detalles = []

for e in all_events:
    d = e.get("data", {})
    method = d.get("mfamethod")
    result = d.get("result")
    raw_time = e.get("time")
    readable_time = datetime.fromtimestamp(raw_time / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if raw_time else "N/A"

    if method != "Email OTP":
        continue

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

# 📤 Enviar resumen en bloques de 20 eventos
bloques = [detalles[i:i+20] for i in range(0, len(detalles), 20)]
for i, bloque in enumerate(bloques):
    texto = (
        f"*Eventos MFA Email OTP ({total_mfa}) entre {start_dt.strftime('%H:%M')} y {end_dt.strftime('%H:%M')} UTC (bloque {i+1}/{len(bloques)}):*\n"
        f"• Success: {success_count}\n"
        f"• Sent: {sent_count}\n"
        f"• Failure: {failure_count}\n\n"
        + "\n".join(bloque)
    )
    resp = requests.post(SLACK_WEBHOOK_URL, data=json.dumps({"text": texto}), headers={"Content-Type": "application/json"})
    if resp.status_code == 200:
        print(f"📤 Bloque {i+1} enviado a Slack")
    else:
        print(f"❌ Error al enviar bloque {i+1}: {resp.status_code}")
        print(resp.text)

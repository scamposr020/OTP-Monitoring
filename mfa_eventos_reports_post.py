import os
import requests
import json
from datetime import datetime, timedelta, timezone

# 🔧 Configuración desde entorno
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

# 📅 Rango de fechas (últimos 7 días)
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

# 🔍 Inicializar exportación
report_url = f"{TENANT_URL}/v1.0/reports/mfa_activity"
headers_api = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# 📥 Parámetros iniciales
SIZE = 1000
from_value = start_epoch
to_value = end_epoch
sort_order = "asc"
sort_by = "time"
all_records = []
last_id = None
total_expected = None

while True:
    body = {
        "FROM": str(from_value),
        "TO": str(to_value),
        "SIZE": str(SIZE),
        "SORT_BY": sort_by,
        "SORT_ORDER": sort_order
    }

    resp = requests.post(report_url, headers=headers_api, json=body)
    resp.raise_for_status()
    data = resp.json()

    report = data.get("response", {}).get("report", {})
    hits = report.get("hits", [])
    total = report.get("total", 0)

    if total_expected is None:
        total_expected = total
        print(f"📊 Total esperado: {total_expected}")

    if not hits:
        print("⚠️ No se recibieron más registros.")
        break

    for record in hits:
        if last_id != record["sort"][1]:
            all_records.append(record)
        else:
            print("⚠️ Registro duplicado detectado, omitido.")

    last_sort = hits[-1]["sort"]
    from_value = last_sort[0]
    last_id = last_sort[1]

    print(f"📥 Registros acumulados: {len(all_records)}")

    if len(all_records) >= total_expected:
        print("✅ Todos los registros han sido recuperados.")
        break

# 📤 Exportar a archivo JSON (opcional)
with open("mfa_activity_full.json", "w", encoding="utf-8") as f:
    json.dump(all_records, f, indent=2)
    print("📁 Archivo exportado: mfa_activity_full.json")

import os
import requests
from datetime import datetime, timedelta, timezone

# 🔧 Environment variables
TENANT_URL = os.environ["TENANT_URL"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]

# 🔐 Get access token
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

# 🕒 Time range: last 1 hour (UTC)
now_utc = datetime.now(timezone.utc)
start_utc = now_utc - timedelta(hours=1)

# Convert to EST (UTC-5)
EST = timezone(timedelta(hours=-5))
start_est = start_utc.astimezone(EST)
end_est = now_utc.astimezone(EST)

start_epoch = int(start_utc.timestamp() * 1000)
end_epoch = int(now_utc.timestamp() * 1000)

# 🔍 Query events
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

# 📊 Count results
events = data.get("response", {}).get("events", {}).get("events", [])
total = len(events)
success = sum(1 for e in events if e.get("data", {}).get("result", "").lower() == "success")
failure = sum(1 for e in events if e.get("data", {}).get("result", "").lower() == "failure")
sent = sum(1 for e in events if e.get("data", {}).get("result", "").lower() == "sent")

# 📝 Format Slack message
summary = (
    f"*MFA Event Summary (Last Hour – EST)*\n"
    f"🕒 From: {start_est.strftime('%Y-%m-%d %I:%M:%S %p')} EST\n"
    f"🕒 To:   {end_est.strftime('%Y-%m-%d %I:%M:%S %p')} EST\n\n"
    f"🔍 Total events: *{total}*\n"
    f"✅ Success: *{success}*\n"
    f"❌ Failure: *{failure}*\n"
    f"📨 Sent: *{sent}*"
)

# 📤 Send to Slack
slack_payload = {"text": summary}
slack_resp = requests.post(SLACK_WEBHOOK_URL, json=slack_payload)
slack_resp.raise_for_status()

print("✅ Summary sent to Slack successfully.")
print(summary)

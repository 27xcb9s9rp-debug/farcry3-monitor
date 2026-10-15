import json
import os
import urllib.request
import urllib.error

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

print("Testing Discord webhook...")
print("Webhook starts with:", WEBHOOK_URL[:40])

payload = {
    "content": "✅ Far Cry 3 webhook test from GitHub Actions"
}

body = json.dumps(payload).encode("utf-8")

request = urllib.request.Request(
    WEBHOOK_URL,
    data=body,
    headers={
        "Content-Type": "application/json"
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=20) as response:
        print("SUCCESS")
        print("HTTP status:", response.status)

except urllib.error.HTTPError as e:
    print("FAILED")
    print("HTTP status:", e.code)

    print("Response headers:")
    print(e.headers)

    try:
        print("Response body:")
        print(repr(e.read().decode("utf-8", errors="replace")))
    except Exception as ex:
        print("Could not read response body:", ex)

    raise

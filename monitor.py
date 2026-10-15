import json
import os
import urllib.error
import urllib.request

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"].strip()

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
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=20) as response:
        print("SUCCESS")
        print("HTTP status:", response.status)

except urllib.error.HTTPError as error:
    print("FAILED")
    print("HTTP status:", error.code)
    print("Response headers:")
    print(error.headers)

    body = error.read().decode("utf-8", errors="replace")
    print("Response body:", repr(body))

    raise

import json
import os
import sys
import traceback
import urllib.request
import urllib.error
from pathlib import Path

API_URL = "https://kadabra.warehouse.games/servers/quazal/farcry3/pc"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
STATE_FILE = Path("state.json")


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FarCry3-Discord-Monitor/1.0"},
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def send_discord(message, color):
    payload = {
        "username": "Far Cry 3 Monitor",
        "allowed_mentions": {"parse": []},
        "embeds": [{
            "title": "Far Cry 3 — Quazal PC",
            "description": message,
            "color": color,
            "url": API_URL,
            "footer": {"text": "Server status monitor"},
        }],
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

    print("Sending Discord notification...")

    try:
        with urllib.request.urlopen(
            request,
            timeout=20
        ) as response:

            print(
                f

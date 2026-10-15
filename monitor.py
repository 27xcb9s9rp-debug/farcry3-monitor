import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

API_URL = "https://kadabra.warehouse.games/servers/quazal/farcry3/pc"
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"].strip()
STATE_FILE = Path("state.json")


def get_json(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FarCry3-Discord-Monitor/1.0"
        },
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
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            ),
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status not in (200, 204):
            raise RuntimeError(
                f"Discord returned HTTP {response.status}"
            )


def main():
    data = get_json(API_URL)
    server = data.get("server", {})

    status = str(
        server.get("status", "unknown")
    ).lower()

    players = server.get("player_count")

    if players is None:
        raise ValueError(
            "JSON has no server.player_count field"
        )

    players = int(players)

    if players < 0:
        raise ValueError(
            "Invalid negative player count"
        )

    current = {
        "status": status,
        "player_count": players,
    }

    previous = None

    if STATE_FILE.exists():
        previous = json.loads(
            STATE_FILE.read_text()
        )

    # First run creates baseline only
    if previous is None:
        STATE_FILE.write_text(
            json.dumps(
                current,
                indent=2
            ) + "\n"
        )

        print(
            "Initial baseline saved; no announcement sent."
        )
        return

    old_status = previous.get("status")
    old_players = previous.get("player_count")

    changes = []

    if old_status != status:
        changes.append(
            f"**Status:** "
            f"{old_status.upper()} → "
            f"{status.upper()}"
        )

    if old_players != players:
        changes.append(
            f"**Players:** "
            f"{old_players} → "
            f"{players}"
        )

    if not changes:
        print("No change detected.")
        return

    icon = (
        "🟢"
        if status == "online"
        else "🔴"
    )

    message = (
        f"{icon} **Server update detected**\n\n"
        + "\n".join(changes)
        + f"\n\n{API_URL}"
    )

    color = (
        0x2ECC71
        if status == "online"
        else 0xE74C3C
    )

    # Send before saving state.
    # If Discord fails, state remains unchanged and retry occurs next run.
    send_discord(message, color)

    STATE_FILE.write_text(
        json.dumps(
            current,
            indent=2
        ) + "\n"
    )

    print(
        "Change announced and state saved."
    )


if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print(
            f"Monitor failed: {error}",
            file=sys.stderr
        )
        sys.exit(1)

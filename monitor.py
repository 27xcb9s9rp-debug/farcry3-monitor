import json
import os
import sys
import urllib.request
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


def escape_discord_markdown(text):
    """Prevent player names from changing Discord formatting."""
    text = str(text)

    for character in ("\\", "*", "_", "~", "`", "|", ">"):
        text = text.replace(character, f"\\{character}")

    return text


def send_discord(message, color):
    payload = {
        "username": "Far Cry 3 Monitor",
        "allowed_mentions": {
            "parse": []
        },
        "embeds": [{
            "title": "Far Cry 3 — Quazal PC",
            "description": message,
            "color": color,
            "footer": {
                "text": "Multiplayer Monitor"
            },
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


def create_player_map(players):
    """
    Convert the API player list into:

    {
        "2007": "JustSiarzhuk",
        "2753": "fivcas0"
    }
    """
    player_map = {}

    for index, player in enumerate(players):
        if not isinstance(player, dict):
            continue

        player_id = player.get("id")
        player_name = player.get("name")

        if not player_name:
            player_name = "Unknown player"

        # Use the player ID as the stable identifier.
        # Fall back to the name and position if no ID exists.
        if player_id is None:
            player_id = f"name:{player_name}:{index}"

        player_map[str(player_id)] = str(player_name)

    return player_map


def format_player_list(players):
    """Create a complete Discord-formatted player list."""
    if not players:
        return "No players online."

    sorted_players = sorted(
        players.values(),
        key=lambda name: name.casefold()
    )

    player_lines = [
        f"• {escape_discord_markdown(name)}"
        for name in sorted_players
    ]

    return "\n".join(player_lines)


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(
            state,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )


def main():
    data = get_json(API_URL)
    server = data.get("server", {})

    status = str(
        server.get("status", "unknown")
    ).lower()

    reported_player_count = server.get("player_count")
    player_list = server.get("players", [])

    if reported_player_count is None:
        raise ValueError(
            "JSON has no server.player_count field"
        )

    if not isinstance(player_list, list):
        raise ValueError(
            "JSON server.players field is not a list"
        )

    reported_player_count = int(reported_player_count)

    if reported_player_count < 0:
        raise ValueError(
            "Invalid negative player count"
        )

    current_players = create_player_map(player_list)

    current = {
        "status": status,
        "player_count": reported_player_count,
        "players": current_players,
    }

    # First run: establish a baseline without sending anything.
    if not STATE_FILE.exists():
        save_state(current)

        print(
            "Initial baseline saved; "
            "no announcement sent."
        )
        return

    previous = json.loads(
        STATE_FILE.read_text(encoding="utf-8")
    )

    old_player_count = int(
        previous.get("player_count", 0)
    )

    previous_players_data = previous.get("players")

    # Migrate an older state.json that only stored player_count.
    if not isinstance(previous_players_data, dict):
        previous_players_data = {}

    previous_players = {
        str(player_id): str(player_name)
        for player_id, player_name
        in previous_players_data.items()
    }

    previous_ids = set(previous_players.keys())
    current_ids = set(current_players.keys())

    joined_ids = sorted(
        current_ids - previous_ids
    )

    left_ids = sorted(
        previous_ids - current_ids
    )

    renamed_ids = sorted(
        player_id
        for player_id in current_ids & previous_ids
        if current_players[player_id]
        != previous_players[player_id]
    )

    session_started = (
        old_player_count == 0
        and reported_player_count > 0
    )

    session_ended = (
        old_player_count > 0
        and reported_player_count == 0
    )

    messages = []

    # Session start
    if session_started:
        messages.append(
            "🎮 **Multiplayer game started!**\n"
            "Join the game!"
        )

    # Players who joined
    for player_id in joined_ids:
        player_name = escape_discord_markdown(
            current_players[player_id]
        )

        messages.append(
            f"🌴 **{player_name}** joined the game!"
        )

    # Players who left
    for player_id in left_ids:
        player_name = escape_discord_markdown(
            previous_players[player_id]
        )

        messages.append(
            f"🛶 **{player_name}** left the game."
        )

    # Player name changes
    for player_id in renamed_ids:
        old_name = escape_discord_markdown(
            previous_players[player_id]
        )

        new_name = escape_discord_markdown(
            current_players[player_id]
        )

        messages.append(
            f"✏️ **{old_name}** is now **{new_name}**."
        )

    # Session end
    if session_ended:
        messages.append(
            "🏁 **Multiplayer game ended**"
        )

    # Nothing relevant changed.
    if not messages:
        save_state(current)

        print(
            "No player joins, leaves, name changes, "
            "or session changes detected."
        )
        return

    # Recruitment message when only 1–2 players are online.
    if 1 <= reported_player_count <= 2:
        messages.append(
            "🔥 **Rook Island needs reinforcements!**\n"
            "Join the fun!"
        )

    # Add the complete current player list.
    if reported_player_count > 0:
        formatted_players = format_player_list(
            current_players
        )

        messages.append(
            f"👥 **Players online "
            f"({reported_player_count})**\n"
            f"{formatted_players}"
        )
    else:
        messages.append(
            "👥 **Players online (0)**\n"
            "No players online."
        )

    message = "\n\n".join(messages)

    # Select embed color.
    if session_ended:
        color = 0xE74C3C
    elif joined_ids or session_started:
        color = 0x2ECC71
    else:
        color = 0xF39C12

    # Send first. If Discord fails, do not save the new state,
    # allowing the next run to retry the notification.
    send_discord(message, color)

    save_state(current)

    print(
        "Player update announced and state saved."
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

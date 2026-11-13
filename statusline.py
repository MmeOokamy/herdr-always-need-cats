#!/usr/bin/env python3
"""Status line de Claude Code : fournit les chiffres d'usage au chat de Herdr.

Claude Code lance ce script à chaque rafraîchissement de sa status line et lui
donne sur l'entrée standard un JSON qui contient les limites d'usage du compte
(`rate_limits` : session de 5 heures et semaine). Le script les enregistre dans
~/.cache/usage-cat/state.json, que le mod usage-cat relit, et affiche une
ligne de résumé.

Le fichier a le même format que celui de we-always-need-cats : l'une ou
l'autre des deux status lines peut alimenter le mod.
"""

import json
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "usage-cat")
STATE = os.path.join(CACHE, "state.json")
WINDOWS = ("five_hour", "seven_day")

SETTINGS = {
    "lang": "fr",
    "warn": 50,
    "alert": 80,
    "critical": 95,
    "statusline": True,  # false : enregistre les chiffres sans rien afficher
}
TEXTS = {
    "fr": {"five_hour": "Session", "seven_day": "Semaine", "status": "{label} {pct} %",
           "waiting": "en attente de Claude Code…", "days": ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]},
    "en": {"five_hour": "Session", "seven_day": "Week", "status": "{label} {pct}%",
           "waiting": "waiting for Claude Code…", "days": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]},
}


def load_settings():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            SETTINGS.update(data)
    except (OSError, ValueError):
        pass
    return TEXTS.get(str(SETTINGS["lang"]).lower(), TEXTS["fr"])


def to_epoch(value):
    """Heure de reset en secondes depuis l'epoch (Claude Code envoie des secondes)."""
    if isinstance(value, (int, float)):
        return value / 1000 if value > 1e11 else value
    if isinstance(value, str):
        from datetime import datetime

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def claude_pid():
    """Remonte les processus parents jusqu'à Claude Code."""
    pid = os.getppid()
    for _ in range(8):
        try:
            with open(f"/proc/{pid}/comm") as f:
                name = f.read().strip()
            with open(f"/proc/{pid}/stat") as f:
                parent = int(f.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError, IndexError):
            return 0
        if name in ("claude", "node"):
            return pid
        if parent <= 1:
            return 0
        pid = parent
    return 0


def read_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, ValueError):
        return {}
    return state if isinstance(state, dict) else {}


def write_state(state):
    os.makedirs(CACHE, exist_ok=True)
    temporary = f"{STATE}.{os.getpid()}.tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(temporary, STATE)


def update_state(event, now):
    state = read_state()
    limits = event.get("rate_limits")
    if isinstance(limits, dict):
        for name in WINDOWS:
            data = limits.get(name)
            if isinstance(data, dict) and data.get("used_percentage") is not None:
                state[name] = {
                    "pct": float(data["used_percentage"]),
                    "resets_at": to_epoch(data.get("resets_at")),
                }
    # Sans limites (début de session), les dernières valeurs connues restent.
    state["ts"] = now
    state["pid"] = claude_pid()
    write_state(state)
    return state


def window(state, name, now):
    """(pourcentage utilisé, heure de reset), (0, None) si le reset est passé."""
    data = state.get(name)
    if not isinstance(data, dict) or data.get("pct") is None:
        return None, None
    reset = data.get("resets_at")
    if reset and now >= reset:
        return 0, None
    return min(100, max(0, int(data["pct"]))), reset


def color_of(pct):
    if pct >= SETTINGS["alert"]:
        return 31
    return 33 if pct >= SETTINGS["warn"] else 32


def format_reset(reset, now, text):
    then, today = time.localtime(reset), time.localtime(now)
    clock = time.strftime("%H:%M", then)
    if (then.tm_year, then.tm_yday) == (today.tm_year, today.tm_yday):
        return clock
    return f"{text['days'][then.tm_wday]} {clock}"


def status_text(state, now, text):
    """Une ligne : Session 42 % ↻ 14:00 · Semaine 12 %"""
    parts = []
    for name in WINDOWS:
        pct, reset = window(state, name, now)
        if pct is None:
            continue
        line = text["status"].format(label=text[name], pct=pct)
        if reset and name == "five_hour":
            line += f" ↻ {format_reset(reset, now, text)}"
        parts.append(f"\033[{color_of(pct)}m{line}\033[0m")
    return " · ".join(parts) if parts else text["waiting"]


def main():
    text = load_settings()
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    if not isinstance(event, dict):
        event = {}
    now = time.time()
    state = update_state(event, now)
    if SETTINGS["statusline"]:
        print(status_text(state, now, text))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)

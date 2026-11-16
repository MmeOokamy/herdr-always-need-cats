#!/usr/bin/env python3
"""Claude Code status line: provides the usage figures to the Herdr cat.

Claude Code runs this script on every refresh of its status line and passes
it on standard input a JSON that contains the account's usage limits
(`rate_limits`: 5-hour session and week). The script saves them in
~/.cache/usage-cat/state.json, which the usage-cat mod reads, and prints a
summary line.

The file has the same format as the one from we-always-need-cats: either of
the two status lines can feed the mod.
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
    "statusline": True,  # false: saves the figures without printing anything
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
    """Reset time in seconds since the epoch (Claude Code sends seconds)."""
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
    """Walks up the parent processes to Claude Code."""
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
    # Without limits (start of a session), the last known values remain.
    state["ts"] = now
    state["pid"] = claude_pid()
    write_state(state)
    return state


def window(state, name, now):
    """(percentage used, reset time), (0, None) if the reset has passed."""
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
    """One line: Session 42 % ↻ 14:00 · Semaine 12 %"""
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

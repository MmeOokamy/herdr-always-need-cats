#!/usr/bin/env python3
"""Claude Code hook: what each session is doing, for the cats strip (strip-cats).

Called by Claude Code on every event (install.py registers it in
~/.claude/settings.json, next to the hooks already in place). In a Herdr
terminal (HC_TERMINAL_ID variable), it writes
~/.cache/herdr-always-need-cats/sessions/<session>.json: the state (working,
waiting for you, done), what the bubble says ("écrit main.js"), the activity
(color of the cat's screen) and the subagents (kittens). Outside Herdr, it
does nothing.

It prints nothing and always exits without error, so as never to disturb
Claude Code. `hook.py --gc` removes the sessions whose process no longer exists.
"""

import fcntl
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(BASE, "config.json")
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "herdr-always-need-cats")
SESSIONS = os.path.join(CACHE, "sessions")
MAX_AGE = 12 * 3600

TEXTS = {
    "fr": {
        "write": "écrit", "read": "lit", "search": "cherche", "run": "lance :",
        "run_any": "lance une commande", "delegate": "délègue à un agent", "web": "navigue sur le web",
        "skill": "charge", "use": "utilise", "a_service": "un service", "work": "travaille",
        "think": "réfléchit", "question": "te pose une question", "plan": "propose un plan",
        "compact": "résume la conversation", "permission": "attend ton accord",
        "answer": "attend ta réponse", "done": "a terminé", "error": "arrêté sur une erreur",
    },
    "en": {
        "write": "writes", "read": "reads", "search": "searches", "run": "runs:",
        "run_any": "runs a command", "delegate": "delegates to an agent", "web": "browses the web",
        "skill": "loads", "use": "uses", "a_service": "a service", "work": "works",
        "think": "thinks", "question": "asks you a question", "plan": "proposes a plan",
        "compact": "sums up the conversation", "permission": "waits for your approval",
        "answer": "waits for your answer", "done": "is done", "error": "stopped on an error",
    },
}


def texts():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            lang = str(json.load(f).get("lang", "fr")).lower()
    except (OSError, ValueError, AttributeError):
        lang = "fr"
    return TEXTS.get(lang, TEXTS["fr"])


def short(text, length=60):
    text = " ".join(str(text or "").split())
    return text if len(text) <= length else text[: length - 1] + "…"


def tool_detail(tool_input):
    """Short summary of what the tool does (file, command, search)."""
    if not isinstance(tool_input, dict):
        return ""
    for key in ("file_path", "notebook_path", "path"):
        if tool_input.get(key):
            return os.path.basename(str(tool_input[key]).rstrip("/"))
    for key in ("description", "command", "pattern", "query", "url", "skill", "prompt"):
        if tool_input.get(key):
            return short(tool_input[key], 40)
    return ""


def describe_tool(t, tool, detail):
    """Bubble text and activity (screen color) for a tool."""
    if tool in ("Edit", "Write", "NotebookEdit"):
        return f"{t['write']} {detail}".strip(), "write"
    if tool == "Read":
        return f"{t['read']} {detail}".strip(), "read"
    if tool in ("Grep", "Glob", "ToolSearch"):
        return f"{t['search']} {detail}".strip(), "read"
    if tool == "Bash":
        return (f"{t['run']} {detail}" if detail else t["run_any"]), "shell"
    if tool in ("Agent", "Task", "Workflow"):
        return t["delegate"], "agent"
    if tool in ("WebSearch", "WebFetch"):
        return t["web"], "web"
    if tool == "Skill":
        return f"{t['skill']} {detail}".strip(), "think"
    if tool.startswith("mcp__"):
        parts = tool.split("__")
        return f"{t['use']} {parts[1] if len(parts) > 1 else t['a_service']}", "web"
    return (f"{t['use']} {tool}" if tool else t["work"]), "think"


def claude_pid():
    """Walks up the parent processes to Claude Code, to know when it stops."""
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


def session_path(session):
    safe = "".join(c for c in session if c.isalnum() or c in "-_")[:80]
    return os.path.join(SESSIONS, f"{safe}.json")


def gc():
    now = time.time()
    try:
        names = os.listdir(SESSIONS)
    except OSError:
        return
    for name in names:
        path = os.path.join(SESSIONS, name)
        try:
            if not name.endswith(".json"):
                if now - os.path.getmtime(path) > 60:
                    os.unlink(path)  # abandoned temporary file
                continue
            with open(path, encoding="utf-8") as f:
                cat = json.load(f)
            pid = int(cat.get("pid") or 0)
            if (pid and not os.path.exists(f"/proc/{pid}")) or now - cat.get("seen", 0) > MAX_AGE:
                os.unlink(path)
        except (OSError, ValueError):
            try:
                os.unlink(path)
            except OSError:
                pass


def set_state(cat, state, text="", activity="think"):
    if cat.get("state") != state:
        cat["since"] = time.time()
    cat["state"], cat["text"], cat["activity"] = state, text, activity


def apply(cat, e, t):
    """Updates a cat's state according to a Claude Code event."""
    event = e.get("hook_event_name") or ""
    agent = e.get("agent_id") or ""
    agent_type = e.get("agent_type") or ""
    tool = e.get("tool_name") or ""
    detail = tool_detail(e.get("tool_input"))
    kittens = cat.setdefault("kittens", {})
    cwd = e.get("cwd") or ""
    if cwd and not agent and (not cat.get("project") or event == "SessionStart"):
        cat["project"] = os.path.basename(cwd.rstrip("/")) or cwd

    if event == "SubagentStart":
        kittens[agent or f"agent-{len(kittens)}"] = {"type": agent_type, "activity": "think"}
    elif event == "SubagentStop":
        if agent in kittens:
            del kittens[agent]
        elif kittens and not agent:
            kittens.pop(next(iter(kittens)))
    elif agent:
        # Subagent event: only its kitten changes activity.
        kitten = kittens.setdefault(agent, {"type": agent_type, "activity": "think"})
        if event == "PreToolUse":
            kitten["activity"] = describe_tool(t, tool, "")[1]
        elif event in ("PostToolUse", "PostToolUseFailure"):
            kitten["activity"] = "think"
    elif event == "UserPromptSubmit":
        set_state(cat, "work", t["think"])
    elif event == "PreToolUse":
        if tool == "AskUserQuestion":
            set_state(cat, "question", t["question"])
        elif tool == "ExitPlanMode":
            set_state(cat, "question", t["plan"])
        else:
            set_state(cat, "work", *describe_tool(t, tool, detail))
    elif event in ("PostToolUse", "PostToolUseFailure"):
        set_state(cat, "work", t["think"])
    elif event == "PreCompact":
        set_state(cat, "work", t["compact"])
    elif event == "Notification":
        kind = e.get("notification_type") or ""
        text = str(e.get("message") or "").lower()
        if kind == "permission_prompt" or (not kind and "permission" in text):
            set_state(cat, "question", t["permission"])
        elif kind == "elicitation_dialog":
            set_state(cat, "question", t["question"])
        elif kind == "idle_prompt" or (not kind and "waiting for your input" in text):
            if cat.get("state") == "work":
                set_state(cat, "question", t["answer"])
    elif event == "Stop":
        set_state(cat, "done", t["done"])
        kittens.clear()
    elif event == "StopFailure":
        set_state(cat, "question", t["error"])


def record(e, terminal):
    event = e.get("hook_event_name") or ""
    session = e.get("session_id") or ""
    if not event or not session:
        return
    os.makedirs(SESSIONS, exist_ok=True)
    path = session_path(session)
    with open(os.path.join(CACHE, "sessions.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if event == "SessionEnd":
            try:
                os.unlink(path)
            except OSError:
                pass
            return
        try:
            with open(path, encoding="utf-8") as f:
                cat = json.load(f)
        except (OSError, ValueError):
            cat = {"sid": session, "state": "idle", "text": "", "activity": "think", "kittens": {}, "since": time.time()}
        cat["terminal"] = terminal
        cat["seen"] = time.time()
        pid = claude_pid()
        if pid:
            cat["pid"] = pid
        apply(cat, e, texts())
        tmp = f"{path}.{os.getpid()}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cat, f, ensure_ascii=False)
        os.replace(tmp, path)
        if event == "SessionStart":
            gc()


def main():
    if "--gc" in sys.argv:
        os.makedirs(CACHE, exist_ok=True)
        with open(os.path.join(CACHE, "sessions.lock"), "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            gc()
        return
    raw = sys.stdin.buffer.read()
    terminal = os.environ.get("HC_TERMINAL_ID") or ""
    if not terminal:
        return  # outside Herdr: nothing to do (the other hooks receive the event)
    try:
        e = json.loads(raw)
    except ValueError:
        return
    if isinstance(e, dict):
        record(e, terminal)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)

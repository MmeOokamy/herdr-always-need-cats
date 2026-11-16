#!/usr/bin/env python3
"""Liste les sessions Claude Code enregistrées, pour le mod claude-sessions.

Lit ~/.claude/projects/<projet>/<session>.jsonl (une session par fichier) et
écrit sur la sortie standard un JSON :

    {"sessions": [{"id", "cwd", "project", "title", "prompt", "first",
                   "branch", "started", "updated", "prompts", "running",
                   "terminal"}, ...]}

trié de la plus récente à la plus ancienne. Les fichiers font parfois
plusieurs Mo : ce qui en est tiré est gardé dans
~/.cache/herdr-always-need-cats/sessions.json, et un fichier n'est relu que
si sa taille ou sa date a changé.

Avec --delete <id> : met la session à la corbeille (gio trash ; sans gio,
la supprime) : son fichier, son dossier (sous-agents), et ses dossiers
~/.claude/file-history/<id> et ~/.claude/session-env/<id>. Refusé si la
session est ouverte. Écrit {"deleted": [chemins]} ou {"error": "..."}.

Une session est « running » quand un processus Claude Code vivant la déclare
dans ~/.claude/sessions/<pid>.json ; « terminal » est alors l'adresse du
terminal Herdr qui la porte (variable HC_TERMINAL_ID du processus), ou null
si elle tourne hors de Herdr.
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
PROJECTS = os.path.join(HOME, ".claude", "projects")
LIVE = os.path.join(HOME, ".claude", "sessions")
CACHE = os.path.join(HOME, ".cache", "herdr-always-need-cats", "sessions.json")
CLAUDE = os.path.join(HOME, ".claude")
SESSION_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
CACHE_VERSION = 1
TEXT_MAX = 200

# Messages utilisateur qui ne sont pas des demandes : commandes, rappels,
# reprises automatiques.
NOT_A_PROMPT = (
    "<command-", "<local-command", "<system-reminder", "<bash-", "<task-notification",
    "Caveat:", "[Request interrupted",
)


def short(text):
    text = " ".join(str(text).split())
    return text if len(text) <= TEXT_MAX else text[: TEXT_MAX - 1] + "…"


def prompt_text(message):
    """Texte tapé par la personne, ou None (résultat d'outil, commande...)."""
    content = (message or {}).get("content")
    if isinstance(content, list):
        parts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        content = "\n".join(parts)
    if not isinstance(content, str):
        return None
    content = content.strip()
    if not content or content.startswith(NOT_A_PROMPT):
        return None
    return content


def read_session(path):
    """Ce qui sert à la liste, tiré d'un fichier de session."""
    info = {
        "cwd": None, "branch": None, "ai_title": None, "name": None,
        "first": None, "prompt": None, "started": None, "updated": None, "prompts": 0,
    }
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            # Ne décoder que les lignes utiles : les autres peuvent être énormes.
            if '"type":"user"' in line:
                kind = "user"
            elif '"type":"ai-title"' in line:
                kind = "ai-title"
            elif '"type":"agent-name"' in line:
                kind = "agent-name"
            elif '"type":"last-prompt"' in line:
                kind = "last-prompt"
            else:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if not isinstance(record, dict) or record.get("type") != kind:
                continue
            if kind == "ai-title" and record.get("aiTitle"):
                info["ai_title"] = short(record["aiTitle"])
            elif kind == "agent-name" and record.get("agentName"):
                info["name"] = short(record["agentName"])
            elif kind == "last-prompt" and record.get("lastPrompt"):
                info["prompt"] = short(record["lastPrompt"])
            elif kind == "user":
                if record.get("isSidechain"):
                    continue
                stamp = record.get("timestamp")
                if stamp:
                    info["started"] = info["started"] or stamp
                    info["updated"] = stamp
                if record.get("cwd") and not info["cwd"]:
                    info["cwd"] = record["cwd"]
                if record.get("gitBranch"):
                    info["branch"] = record["gitBranch"]
                if record.get("isMeta"):
                    continue
                text = prompt_text(record.get("message"))
                if text:
                    info["prompts"] += 1
                    info["first"] = info["first"] or short(text)
    return info


def load_cache():
    try:
        with open(CACHE, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict) or data.get("version") != CACHE_VERSION:
        return {}
    files = data.get("files")
    return files if isinstance(files, dict) else {}


def save_cache(files):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    temporary = CACHE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump({"version": CACHE_VERSION, "files": files}, f, ensure_ascii=False)
    os.replace(temporary, CACHE)


def live_sessions():
    """Sessions ouvertes : {id de session: adresse du terminal Herdr ou None}."""
    live = {}
    for path in glob.glob(os.path.join(LIVE, "*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            pid = int(data["pid"])
            session = str(data["sessionId"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        except PermissionError:
            pass
        terminal = None
        try:
            with open(f"/proc/{pid}/environ", "rb") as f:
                for item in f.read().split(b"\0"):
                    if item.startswith(b"HC_TERMINAL_ID="):
                        terminal = item.split(b"=", 1)[1].decode() or None
        except OSError:
            pass  # hors Linux, ou processus d'un autre utilisateur
        live[session] = terminal
    return live


def session_paths(session_id):
    """Tout ce qui appartient à une session, parmi ce qui existe."""
    paths = []
    for project in glob.glob(os.path.join(glob.escape(PROJECTS), "*")):
        paths += [os.path.join(project, session_id + ".jsonl"), os.path.join(project, session_id)]
    paths += [os.path.join(CLAUDE, "file-history", session_id), os.path.join(CLAUDE, "session-env", session_id)]
    return [p for p in paths if os.path.lexists(p)]


def delete(session_id):
    if not SESSION_ID.match(session_id):
        return {"error": f"identifiant invalide : {session_id}"}
    if session_id in live_sessions():
        return {"error": "session ouverte : la fermer avant de la supprimer"}
    paths = session_paths(session_id)
    if not any(p.endswith(".jsonl") for p in paths):
        return {"error": "session introuvable"}
    gio = shutil.which("gio")
    for path in paths:
        if gio:
            result = subprocess.run([gio, "trash", path], capture_output=True, text=True)
            if result.returncode != 0:
                return {"error": result.stderr.strip() or f"gio trash {path} en échec"}
        elif os.path.isdir(path) and not os.path.islink(path):
            shutil.rmtree(path)
        else:
            os.unlink(path)
    return {"deleted": paths, "trash": bool(gio)}


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--delete":
        json.dump(delete(sys.argv[2]), sys.stdout, ensure_ascii=False)
        return
    cached = load_cache()
    files = {}
    changed = False
    for path in glob.glob(os.path.join(glob.escape(PROJECTS), "*", "*.jsonl")):
        try:
            stat = os.stat(path)
        except OSError:
            continue
        key = f"{stat.st_size}:{int(stat.st_mtime)}"
        entry = cached.get(path)
        if not entry or entry.get("key") != key:
            try:
                entry = {"key": key, "info": read_session(path), "mtime": stat.st_mtime}
            except OSError:
                continue
            changed = True
        files[path] = entry
    if changed or len(files) != len(cached):
        try:
            save_cache(files)
        except OSError:
            pass

    live = live_sessions()
    sessions = []
    for path, entry in files.items():
        info = entry["info"]
        if not info["prompts"] or not info["cwd"]:
            continue  # session vide (ouverte puis quittée)
        session_id = os.path.splitext(os.path.basename(path))[0]
        sessions.append({
            "id": session_id,
            "cwd": info["cwd"],
            "project": os.path.basename(info["cwd"].rstrip("/")) or info["cwd"],
            "title": info["name"] or info["ai_title"] or info["first"],
            "prompt": info["prompt"],
            "first": info["first"],
            "branch": info["branch"] if info["branch"] not in (None, "", "HEAD") else None,
            "started": info["started"],
            "updated": entry["mtime"],
            "prompts": info["prompts"],
            "running": session_id in live,
            "terminal": live.get(session_id),
        })
    sessions.sort(key=lambda s: s["updated"], reverse=True)
    json.dump({"sessions": sessions}, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()

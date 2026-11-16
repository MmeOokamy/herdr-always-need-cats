#!/usr/bin/env python3
"""Installs the cats in Herdr.

1. Generates the animated images (tools/make_sprites.py) if they are missing.
2. Links the mods usage-cat, agents-cats, toast-cats, claude-sessions,
   sessions-footer, strip-cats and pane-cats into ~/.config/herdr-app/mods
   (symbolic links: a change made here is picked up live).
3. Creates the "main-usage-cat" layout: a copy of Herdr's "main" layout (which
   cannot be modified) with the usage cat in the sidebar, between Spaces and
   Agents, the agent list replaced by agents-cats and notifications
   shown by toast-cats, the sidebar footer replaced by sessions-footer
   ("sessions" button), the cats strip (strip-cats) above the status bar
   and the pane header replaced by pane-cats; then displays the layout.
4. Adds the shortcuts ctrl-shift-j (list of Claude sessions) and
   alt-shift-p (cats strip menu) to keys.json, if they are free.
5. Registers hook.py as a Claude Code hook, next to the hooks already in
   place (it feeds the cats strip).
6. Registers statusline.py as the Claude Code status line, if no other one
   is installed yet (--statusline to replace the one in place).

Usage: python3 install.py [--statusline]
       python3 install.py --uninstall
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HERDR = os.path.join(os.path.expanduser("~"), ".config", "herdr-app")
MODS = ("usage-cat", "agents-cats", "toast-cats", "claude-sessions", "sessions-footer", "strip-cats", "pane-cats")
LAYOUT = "main-usage-cat"
LAYOUT_FILE = os.path.join(HERDR, "layouts", f"{LAYOUT}.json")
FLOAT_ID = "usage-cat"  # old version: floating block
BLOCK_ID = "usage-cat"
BLOCK_HEIGHT = 112
FOOTER_HEIGHT = 97  # Settings, sessions, Add machine (69 px with two lines)
CONFIG = os.path.join(HERE, "config.json")  # local, ignored by git
CONFIG_EXAMPLE = os.path.join(HERE, "config.example.json")
STATUSLINE = os.path.join(HERE, "statusline.py")
CLAUDE_SETTINGS = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
KEYS_FILE = os.path.join(HERDR, "keys.json")
# (key, action, role): added to keys.json only if the key is free.
KEYBINDINGS = (
    ("ctrl-shift-j", "mod.open:claude-sessions", "sessions Claude"),
    ("alt-shift-p", "strip-cats.pick", "menu de la bande des chats"),
)
STRIP = {"id": "strip-cats", "type": "block", "size": {"px": 128}, "min": 96, "max": 240,
         "content": {"mod": "strip-cats"}}
PANE_HEADER = {"content": {"mod": "pane-cats"}, "reveal": "always", "height": 30, "position": "top"}
HOOK = os.path.join(HERE, "hook.py")
HOOK_COMMAND = f'python3 "{HOOK}"'
HOOK_EVENTS = (
    "PreToolUse", "PostToolUse", "PostToolUseFailure", "UserPromptSubmit", "Notification",
    "Stop", "StopFailure", "SubagentStart", "SubagentStop", "PreCompact", "SessionStart", "SessionEnd",
)
TOOL_EVENTS = ("PreToolUse", "PostToolUse", "PostToolUseFailure")


def herdr(*args):
    result = subprocess.run(["herdr-app", *args], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"herdr-app {' '.join(args)} : {result.stdout.strip()} {result.stderr.strip()}")
    return result.stdout


def find(node, node_id):
    if node.get("id") == node_id:
        return node
    for child in node.get("children", []):
        found = find(child, node_id)
        if found:
            return found
    return None


def pane_frames(node):
    """The pane frames (blocks { "tab": ..., "pane": {...} })."""
    content = node.get("content") or {}
    if content.get("tab") and isinstance(content.get("pane"), dict):
        yield content["pane"]
    for child in node.get("children", []):
        yield from pane_frames(child)


def remove_float(node):
    """Removes the old floating cat from every node."""
    if "floating" in node:
        node["floating"] = [f for f in node["floating"] if f.get("id") != FLOAT_ID]
        if not node["floating"]:
            del node["floating"]
    for child in node.get("children", []):
        remove_float(child)


def read_claude_settings():
    try:
        with open(CLAUDE_SETTINGS, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except ValueError:
        sys.exit(f"{CLAUDE_SETTINGS} n'est pas un JSON valide : à corriger à la main")
    return data if isinstance(data, dict) else {}


def write_claude_settings(data):
    os.makedirs(os.path.dirname(CLAUDE_SETTINGS), exist_ok=True)
    temporary = CLAUDE_SETTINGS + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temporary, CLAUDE_SETTINGS)


def is_ours(status_line):
    return isinstance(status_line, dict) and STATUSLINE in str(status_line.get("command", ""))


def install_statusline(replace):
    """Claude Code status line: statusline.py writes the figures read by
    usage-cat. Another status line already in place is kept (the one from
    we-always-need-cats writes the same file), unless --statusline is given."""
    data = read_claude_settings()
    current = data.get("statusLine")
    if is_ours(current):
        return
    if current and not replace:
        print(f"Status line gardée : {current.get('command') if isinstance(current, dict) else current}")
        print("  (le chat d'usage n'a des chiffres que si elle écrit ~/.cache/usage-cat/state.json ;")
        print("   python3 install.py --statusline pour la remplacer par celle d'ici)")
        return
    data["statusLine"] = {"type": "command", "command": f'python3 "{STATUSLINE}"'}
    write_claude_settings(data)
    print(f"Status line de Claude Code : {STATUSLINE}")


def uninstall_statusline():
    data = read_claude_settings()
    if is_ours(data.get("statusLine")):
        del data["statusLine"]
        write_claude_settings(data)
        print("Status line retirée de Claude Code")


def read_keys():
    try:
        with open(KEYS_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def write_keys(data):
    temporary = KEYS_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temporary, KEYS_FILE)


def install_keys():
    """Project shortcuts, without taking a key that is already in use."""
    data = read_keys()
    if data is None:
        print(f"{KEYS_FILE} illisible : raccourcis non ajoutés")
        for key, action, _role in KEYBINDINGS:
            print(f'  (à ajouter à la main dans "global" : "{key}": "{action}")')
        return
    changed = False
    for key, action, role in KEYBINDINGS:
        sections = [v for v in data.values() if isinstance(v, dict)]
        if any(v.get(key) == action for v in sections):
            continue
        used = next((v[key] for v in sections if key in v), None)
        if used is not None:
            print(f"{key} est déjà pris ({used}) : {role} sans raccourci")
            print(f'  (à lier à une autre touche dans {KEYS_FILE} : "{action}")')
            continue
        data.setdefault("global", {})[key] = action
        changed = True
        print(f"Raccourci ajouté : {key} ({role})")
    if changed:
        write_keys(data)


def uninstall_keys():
    data = read_keys()
    if not data:
        return
    changed = False
    for key, action, _role in KEYBINDINGS:
        for section in data.values():
            if isinstance(section, dict) and section.get(key) == action:
                del section[key]
                changed = True
                print(f"Raccourci retiré : {key}")
    if changed:
        write_keys(data)


def is_our_hook(entry):
    return isinstance(entry, dict) and any(
        isinstance(h, dict) and HOOK in str(h.get("command", "")) for h in entry.get("hooks", []))


def install_hooks():
    """hook.py receives Claude Code events, next to the hooks already in place
    (those of we-always-need-cats keep receiving everything)."""
    data = read_claude_settings()
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        print("hooks de ~/.claude/settings.json illisibles : hook.py non déclaré")
        return
    # The folder the cats strip watches, before the first event.
    os.makedirs(os.path.join(os.path.expanduser("~"), ".cache", "herdr-always-need-cats", "sessions"), exist_ok=True)
    added = []
    for event in HOOK_EVENTS:
        entries = hooks.setdefault(event, [])
        if not isinstance(entries, list) or any(is_our_hook(e) for e in entries):
            continue
        entry = {"hooks": [{"type": "command", "command": HOOK_COMMAND}]}
        if event in TOOL_EVENTS:
            entry = {"matcher": "*", **entry}
        entries.append(entry)
        added.append(event)
    if added:
        write_claude_settings(data)
        print(f"Hooks de Claude Code : {HOOK} ({len(added)} événements)")


def uninstall_hooks():
    data = read_claude_settings()
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return
    changed = False
    for event in list(hooks):
        entries = hooks[event]
        if not isinstance(entries, list):
            continue
        kept = [e for e in entries if not is_our_hook(e)]
        if len(kept) != len(entries):
            changed = True
            if kept:
                hooks[event] = kept
            else:
                del hooks[event]
    if changed:
        if not hooks:
            del data["hooks"]
        write_claude_settings(data)
        print("Hooks de Claude Code retirés")


def install(replace_statusline):
    if not os.path.exists(CONFIG):
        shutil.copyfile(CONFIG_EXAMPLE, CONFIG)
        print(f"Réglages : {CONFIG}")

    missing = [
        mod for mod in ("usage-cat", "agents-cats")  # the mods that have images
        if not os.path.isdir(os.path.join(HERE, mod, "sprites")) or not os.listdir(os.path.join(HERE, mod, "sprites"))
    ]
    if missing:
        subprocess.run([sys.executable, os.path.join(HERE, "tools", "make_sprites.py")], check=True)

    for mod in MODS:
        source = os.path.join(HERE, mod)
        target = os.path.join(HERDR, "mods", mod)
        if os.path.islink(target):
            if os.path.realpath(target) != source:
                sys.exit(f"{target} pointe déjà ailleurs : {os.readlink(target)}")
        elif os.path.exists(target):
            sys.exit(f"{target} existe déjà (pas un lien) : à retirer à la main")
        else:
            os.symlink(source, target)
            print(f"Mod relié : {target}")
        result = subprocess.run(["herdr-app", "check", target], capture_output=True, text=True)
        if result.returncode != 0:
            sys.exit(f"herdr-app check en échec ({mod}) :\n{result.stdout}{result.stderr}")

    if not os.path.exists(LAYOUT_FILE):
        herdr("do", "layout.clone", json.dumps({"name": "main", "as": LAYOUT}))
        print(f"Layout créé : {LAYOUT_FILE}")
    with open(LAYOUT_FILE, encoding="utf-8") as f:
        layout = json.load(f)
    remove_float(layout)
    lists = find(layout, "sidebar-lists")
    if lists is None:
        sys.exit("Noeud sidebar-lists introuvable dans le layout")
    children = [c for c in lists["children"] if c.get("id") != BLOCK_ID]
    position = next((i + 1 for i, c in enumerate(children) if c.get("id") == "spaces"), 0)
    children.insert(position, {
        "id": BLOCK_ID,
        "type": "block",
        "size": {"px": BLOCK_HEIGHT},
        "content": {"mod": "usage-cat", "props": {"config": CONFIG, "root": HERE}},
    })
    lists["children"] = children
    agents = find(layout, "agents")
    if agents is not None:
        agents["content"]["mod"] = "agents-cats"
    footer = find(layout, "sidebar-footer")
    if footer is not None:
        footer["content"] = {"mod": "sessions-footer"}
        footer["size"] = {"px": FOOTER_HEIGHT}
    # The cats strip, at the bottom of the main column, above the status bar.
    work = find(layout, "work")
    if work is not None and find(layout, STRIP["id"]) is None:
        kids = work["children"]
        status = next((i for i, c in enumerate(kids) if c.get("id") == "status"), len(kids))
        kids.insert(status, dict(STRIP))
    # The pane header, where the cat jumps.
    for frame in pane_frames(layout):
        header = frame.get("header")
        if not header:
            frame["header"] = dict(PANE_HEADER)
        elif header.get("content", {}).get("mod") == "pane":
            header["content"]["mod"] = "pane-cats"
    layout["toast"] = "toast-cats"  # key at the root of the layout
    temporary = LAYOUT_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temporary, LAYOUT_FILE)
    # Herdr only reloads a mod when the layout changes: go through main
    # when the layout is already displayed, to load the new versions.
    try:
        shown = json.loads(herdr("status")).get("layout")
    except ValueError:
        shown = None
    if shown == LAYOUT:
        herdr("do", "layout.switch", json.dumps({"name": "main"}))
    herdr("do", "layout.switch", json.dumps({"name": LAYOUT}))
    print(f"Layout affiché : {LAYOUT} (ctrl-shift-l pour changer de layout)")
    install_keys()
    install_hooks()
    install_statusline(replace_statusline)


def uninstall():
    if os.path.exists(LAYOUT_FILE):
        subprocess.run(["herdr-app", "do", "layout.switch", json.dumps({"name": "main"})], capture_output=True)
        os.unlink(LAYOUT_FILE)
        print(f"Layout supprimé : {LAYOUT_FILE}")
    for mod in MODS:
        target = os.path.join(HERDR, "mods", mod)
        if os.path.islink(target):
            os.unlink(target)
            print(f"Mod retiré : {target}")
    uninstall_keys()
    uninstall_hooks()
    uninstall_statusline()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--statusline", action="store_true", help="remplacer la status line déjà en place")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    if args.uninstall:
        uninstall()
    else:
        install(args.statusline)


if __name__ == "__main__":
    main()

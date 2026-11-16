#!/usr/bin/env python3
"""Installe les chats dans Herdr.

1. Génère les images animées (tools/make_sprites.py) si elles manquent.
2. Relie les mods usage-cat, agents-cats, toast-cats et claude-sessions dans
   ~/.config/herdr-app/mods
   (liens symboliques : une modification ici est prise en compte à chaud).
3. Crée le layout « main-usage-cat » : copie du layout Herdr « main » (non
   modifiable) avec le chat d'usage dans la barre latérale, entre Spaces et
   Agents, la liste des agents remplacée par agents-cats et les
   notifications montrées par toast-cats, le pied de la barre latérale
   remplacé par sessions-footer (bouton « sessions ») ; et l'affiche.
4. Ajoute le raccourci ctrl-shift-j (liste des sessions Claude) à
   keys.json, s'il n'est pas déjà pris.
5. Déclare statusline.py comme status line de Claude Code, si aucune autre
   n'est déjà installée (--statusline pour remplacer celle en place).

Usage : python3 install.py [--statusline]
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
MODS = ("usage-cat", "agents-cats", "toast-cats", "claude-sessions", "sessions-footer")
LAYOUT = "main-usage-cat"
LAYOUT_FILE = os.path.join(HERDR, "layouts", f"{LAYOUT}.json")
FLOAT_ID = "usage-cat"  # ancienne version : bloc flottant
BLOCK_ID = "usage-cat"
BLOCK_HEIGHT = 112
FOOTER_HEIGHT = 97  # Settings, sessions, Add machine (69 px avec deux lignes)
CONFIG = os.path.join(HERE, "config.json")  # local, ignoré par git
CONFIG_EXAMPLE = os.path.join(HERE, "config.example.json")
STATUSLINE = os.path.join(HERE, "statusline.py")
CLAUDE_SETTINGS = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
KEYS_FILE = os.path.join(HERDR, "keys.json")
SESSIONS_KEY = "ctrl-shift-j"
SESSIONS_ACTION = "mod.open:claude-sessions"


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


def remove_float(node):
    """Retire l'ancien chat flottant de tous les nœuds."""
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
    """Status line de Claude Code : statusline.py écrit les chiffres lus par
    usage-cat. Une autre status line en place est gardée (celle de
    we-always-need-cats écrit le même fichier), sauf avec --statusline."""
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


def install_key():
    """Raccourci de la liste des sessions Claude, sans prendre une touche déjà utilisée."""
    data = read_keys()
    if data is None:
        print(f"{KEYS_FILE} illisible : raccourci non ajouté")
        print(f'  (à ajouter à la main : "{SESSIONS_KEY}": "{SESSIONS_ACTION}" dans "global")')
        return
    sections = [v for v in data.values() if isinstance(v, dict)]
    if any(v.get(SESSIONS_KEY) == SESSIONS_ACTION for v in sections):
        return
    used = next((v[SESSIONS_KEY] for v in sections if SESSIONS_KEY in v), None)
    if used is not None:
        print(f"{SESSIONS_KEY} est déjà pris ({used}) : sessions Claude sans raccourci")
        print(f'  (à lier à une autre touche dans {KEYS_FILE} : "{SESSIONS_ACTION}")')
        return
    data.setdefault("global", {})[SESSIONS_KEY] = SESSIONS_ACTION
    write_keys(data)
    print(f"Raccourci ajouté : {SESSIONS_KEY} (sessions Claude)")


def uninstall_key():
    data = read_keys()
    if not data:
        return
    changed = False
    for section in data.values():
        if isinstance(section, dict) and section.get(SESSIONS_KEY) == SESSIONS_ACTION:
            del section[SESSIONS_KEY]
            changed = True
    if changed:
        write_keys(data)
        print(f"Raccourci retiré : {SESSIONS_KEY}")


def install(replace_statusline):
    if not os.path.exists(CONFIG):
        shutil.copyfile(CONFIG_EXAMPLE, CONFIG)
        print(f"Réglages : {CONFIG}")

    missing = [
        mod for mod in ("usage-cat", "agents-cats")  # les mods qui ont des images
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
    layout["toast"] = "toast-cats"  # clé de la racine du layout
    temporary = LAYOUT_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temporary, LAYOUT_FILE)
    # Herdr ne recharge un mod qu'au changement de layout : passer par main
    # quand le layout est déjà affiché, pour charger les nouvelles versions.
    try:
        shown = json.loads(herdr("status")).get("layout")
    except ValueError:
        shown = None
    if shown == LAYOUT:
        herdr("do", "layout.switch", json.dumps({"name": "main"}))
    herdr("do", "layout.switch", json.dumps({"name": LAYOUT}))
    print(f"Layout affiché : {LAYOUT} (ctrl-shift-l pour changer de layout)")
    install_key()
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
    uninstall_key()
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

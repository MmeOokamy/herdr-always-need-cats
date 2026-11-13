#!/usr/bin/env python3
"""Installe les chats dans Herdr.

1. Génère les images animées (tools/make_sprites.py) si elles manquent.
2. Relie les mods usage-cat et agents-cats dans ~/.config/herdr-app/mods
   (liens symboliques : une modification ici est prise en compte à chaud).
3. Crée le layout « main-usage-cat » : copie du layout Herdr « main » (non
   modifiable) avec le chat d'usage dans la barre latérale, entre Spaces et
   Agents, et la liste des agents remplacée par agents-cats ; et l'affiche.
4. Déclare statusline.py comme status line de Claude Code, si aucune autre
   n'est déjà installée (--statusline pour remplacer celle en place).

Usage : python3 install.py [--statusline]
        python3 install.py --uninstall
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HERDR = os.path.join(os.path.expanduser("~"), ".config", "herdr-app")
MODS = ("usage-cat", "agents-cats")
LAYOUT = "main-usage-cat"
LAYOUT_FILE = os.path.join(HERDR, "layouts", f"{LAYOUT}.json")
FLOAT_ID = "usage-cat"  # ancienne version : bloc flottant
BLOCK_ID = "usage-cat"
BLOCK_HEIGHT = 112
CONFIG = os.path.join(HERE, "config.json")
STATUSLINE = os.path.join(HERE, "statusline.py")
CLAUDE_SETTINGS = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")


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


def install(replace_statusline):
    missing = [
        mod for mod in MODS
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
        "content": {"mod": "usage-cat", "props": {"config": CONFIG}},
    })
    lists["children"] = children
    agents = find(layout, "agents")
    if agents is not None:
        agents["content"]["mod"] = "agents-cats"
    temporary = LAYOUT_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(temporary, LAYOUT_FILE)
    herdr("do", "layout.switch", json.dumps({"name": LAYOUT}))
    print(f"Layout affiché : {LAYOUT} (ctrl-shift-l pour changer de layout)")
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

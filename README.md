# herdr-always-need-cats

Des chats en pixel art dans l'application Herdr (`~/.config/herdr-app`) : un
chat d'usage dans la barre latérale, et un chat par agent Claude Code dans la
liste des agents. Le projet se suffit à lui-même : il contient ses dessins,
sa status line et ses réglages.

## usage-cat : le chat d'usage dans Herdr

Un chat dans la barre latérale de Herdr, entre Spaces et Agents. Il suit les limites d'usage du compte Claude Code :

- sous le chat, jauge épaisse : la session (fenêtre de 5 heures) ; jauge
  fine : la semaine (7 jours) ;
- à droite : le pourcentage de chaque fenêtre et l'heure de son prochain
  reset (masqué quand la barre latérale est repliée).

| Usage (session ou semaine) | Comportement du chat |
|---|---|
| Moins de 50 % | Assis, jauge verte ; tape sur son ordinateur quand Claude consomme |
| 50 % et plus | Pareil, jauge jaune |
| 80 % et plus | Miaule, point d'exclamation orange, notification Herdr |
| 95 % et plus | Miaule plus vite, en rouge, notification Herdr |
| 100 % | S'endort jusqu'au reset |
| Reset d'une limite presque atteinte | Saute de joie pendant 30 secondes |

### Fonctionnement

- Les chiffres viennent de `~/.cache/usage-cat/state.json`, écrit par
  `statusline.py`, la status line de Claude Code installée par `install.py`.
  Le mod relit ce fichier toutes les 2 secondes.
- Langue, pelage et seuils sont lus dans `config.json` (`lang`, `coat`,
  `warn`, `alert`, `critical`) au démarrage du mod.
- Il signale aussi les mises à jour du projet (voir plus bas).
- Les animations sont des WebP animés, joués nativement par Herdr (pas de
  redessin par timer). Ils sont générés à partir de `tools/drawings.py` par
  `tools/make_sprites.py` : un fichier par pelage, animation et niveau.

### Réglages : `config.json`

`install.py` crée `config.json` à partir de `config.example.json`. Ce fichier
est propre à la machine et ignoré par git : le modifier ne bloque pas les
mises à jour.

| Clé | Défaut | Rôle |
|---|---|---|
| `lang` | `fr` | langue du chat et de la status line : `fr` ou `en` |
| `coat` | `ginger` | pelage : `ginger`, `grey`, `black`, `cream`, `brown` ou `blue` |
| `warn` | `50` | usage (%) à partir duquel la jauge passe au jaune |
| `alert` | `80` | usage (%) à partir duquel le chat miaule |
| `critical` | `95` | usage (%) à partir duquel le chat panique |
| `statusline` | `true` | `false` : la status line enregistre les chiffres sans rien afficher |

Le mod relit ce fichier à son démarrage : relancer Herdr, ou changer de layout
et revenir, après une modification.

## agents-cats : un chat par agent

Copie du mod `agents` de Herdr (la liste des agents de la barre latérale) où
chaque agent Claude Code a pour icône un chat. Chaque
agent a son pelage, fixe pour une même adresse de terminal ; ses sous-agents
sont des chatons. Les autres agents (Codex, etc.) gardent leur icône.

| État Herdr | Chat |
|---|---|
| `working` | tape sur son ordinateur |
| `blocked` (besoin de toi) | miaule |
| `done` | saute de joie |
| `idle` | assis ; endormi après 3 minutes sans activité (sauf l'agent affiché) |

Herdr ne distingue pas « réfléchit » de « travaille » : pas de crêpes ici.

Le mod part de la version 0.1.15 du mod `agents`, gardée pour comparaison dans
`agents-cats/upstream-agents-0.1.15.js.txt`. Les modifications sont marquées
`agents-cats` dans `main.js`. Pour suivre une nouvelle version de Herdr :
comparer ce fichier au nouveau `~/.config/herdr-app/mods/agents/main.js`, puis
reporter les modifications.

## Fichiers

| Chemin | Rôle |
|---|---|
| `usage-cat/main.js` | le mod (gpui-kit) |
| `usage-cat/mod.json` | déclaration du mod |
| `usage-cat/sprites/` | images animées générées |
| `agents-cats/main.js` | liste des agents avec les chats |
| `agents-cats/sprites/` | images animées des chats d'agents |
| `tools/drawings.py` | dessins et couleurs des chats (texte, un caractère par pixel) |
| `tools/make_sprites.py` | génération des images des deux mods (Pillow) |
| `statusline.py` | status line de Claude Code, écrit les chiffres d'usage |
| `updates.py` | vérification et mise à jour depuis les releases GitHub |
| `config.example.json` | réglages par défaut, copiés en `config.json` (local) |
| `install.py` | installation dans Herdr et Claude Code |

## Installation

```bash
python3 install.py
```

Prérequis : Herdr, Python 3.9+, et Pillow pour régénérer les images
(`pip install pillow` ; les images générées sont déjà dans le dossier).

Le script :

1. génère les images si `usage-cat/sprites/` est vide ;
2. crée les liens `~/.config/herdr-app/mods/usage-cat` et `agents-cats` vers
   les dossiers d'ici (les modifications sont prises en compte à chaud) ;
3. vérifie les mods (`herdr-app check`) ;
4. crée le layout `main-usage-cat`, copie du layout `main` de Herdr (qui
   n'est pas modifiable), y ajoute le bloc du chat (112 px de haut) entre
   `spaces` et `agents` dans la barre latérale, remplace la liste des agents
   par `agents-cats`, et l'affiche ;
5. déclare `statusline.py` comme status line de Claude Code
   (`~/.claude/settings.json`), sauf si une autre status line est déjà en
   place : elle est gardée, et le script le signale. `--statusline` la
   remplace.

`ctrl-shift-l` fait passer d'un layout à l'autre.

Après une modification de `tools/drawings.py` :

```bash
python3 tools/make_sprites.py
```

## Mises à jour

Le projet se met à jour depuis le clone git avec lequel il a été installé.
Seules les releases sont proposées, c'est-à-dire les tags `vX.Y.Z` publiés sur
GitHub. Ce qui est fusionné dans `main` entre deux releases attend la suivante.

- **Dans Herdr** : une fois par jour, le chat d'usage vérifie s'il existe une
  nouvelle version. S'il y en a une, il affiche « Mise à jour X.Y.Z
  disponible » sous les jauges (une étiquette « MAJ » sous le chat quand la
  barre latérale est repliée) et envoie une notification. Un clic sur la
  ligne, l'étiquette ou la notification lance la mise à jour, puis une
  notification en donne le résultat.
- **Dans un terminal** :

  ```bash
  python3 updates.py           # vérifie, puis met à jour s'il y a une nouvelle version
  python3 updates.py --check   # vérifie seulement
  ```

Une mise à jour n'écrase rien : c'est une avance rapide du clone jusqu'à la
dernière release (`git merge --ff-only`). Avec des fichiers suivis modifiés
ou des commits locaux, elle s'arrête et le chat affiche « Mise à jour
bloquée » : il faut alors la faire à la main. Après la mise à jour,
`install.py` est relancé pour appliquer un changement de layout ; Herdr
recharge de lui-même les mods dont les fichiers ont changé.

L'état de la dernière vérification est gardé dans
`~/.cache/herdr-always-need-cats/updates.json`.

### Publier une version

Depuis `main` à jour :

```bash
git tag -a v1.1.0 -m "v1.1.0"
git push origin v1.1.0
```

Puis créer la release sur GitHub à partir du tag (Releases, Draft a new
release). Les installations la voient à leur prochaine vérification.

## Désinstallation

```bash
python3 install.py --uninstall
```

Revient au layout `main`, supprime `main-usage-cat` et les liens des mods, et
retire la status line de Claude Code si c'est celle d'ici.

## Limites

- `main-usage-cat` est une copie : les évolutions du layout `main` livrées
  par les mises à jour de Herdr n'y arrivent pas. Pour repartir d'une copie à
  jour : désinstaller puis réinstaller. De même, `agents-cats` ne suit pas
  les évolutions du mod `agents`.
- Claude Code n'a qu'une status line. Le fichier
  `~/.cache/usage-cat/state.json` a le même format que celui de
  `we-always-need-cats` (chats de bureau) : si ce projet est aussi installé,
  sa status line alimente aussi le chat de Herdr, et `install.py` la garde.

## Licence

MIT (voir `LICENSE`), sauf `agents-cats/main.js` et
`agents-cats/upstream-agents-0.1.15.js.txt` : ils reprennent le mod `agents`
de Herdr, sous licence Apache 2.0 (`agents-cats/LICENSE-herdr.txt`). Les
modifications apportées sont marquées `agents-cats` dans `main.js`.

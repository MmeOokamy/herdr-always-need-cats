# herdr-always-need-cats

[English](README.md) | Français

Des chats en pixel art dans l'application Herdr (`~/.config/herdr-app`) :

- un chat d'usage dans la barre latérale ;
- un chat par agent Claude Code dans la liste des agents ;
- des notifications d'agent en forme de chat avec sa bulle ;
- la liste de toutes les sessions Claude Code, pour en reprendre une ;
- une bande en bas de la fenêtre où chaque agent est un chat qui se promène,
  avec un petit chat messager quand il t'attend ou a fini ;
- l'en-tête des volets, où le chat bondit.

Le projet se suffit à lui-même : il contient ses dessins, sa status line et
ses réglages.

## usage-cat : le chat d'usage

Un chat dans la barre latérale de Herdr, entre Spaces et Agents. Il suit les
limites d'usage du compte Claude Code :

- sous le chat, jauge épaisse : la session (fenêtre de 5 heures) ; jauge
  fine : la semaine (7 jours) ;
- à droite : le pourcentage de chaque fenêtre et l'heure de son prochain
  reset (masqué quand la barre latérale est repliée).

| Usage (session ou semaine) | Comportement du chat |
|---|---|
| Moins de 50 % | Assis, jauge verte ; s'occupe quand Claude consomme (voir plus bas) |
| 50 % et plus | Pareil, jauge jaune |
| 80 % et plus | Miaule, point d'exclamation orange, notification Herdr |
| 95 % et plus | Miaule plus vite, en rouge, notification Herdr |
| 100 % | S'endort jusqu'au reset |
| Reset d'une limite presque atteinte | Saute de joie pendant 30 secondes |

Il signale aussi les mises à jour du projet (voir [Mises à jour](#mises-à-jour)).

### Fonctionnement

- Les chiffres viennent de `~/.cache/usage-cat/state.json`, écrit par
  `statusline.py`, la status line de Claude Code installée par `install.py`.
  Le mod relit ce fichier toutes les 2 secondes.
- Langue, pelage et seuils sont lus dans `config.json` au démarrage du mod.
- Les animations sont des WebP animés, joués nativement par Herdr (pas de
  redessin par timer). Ils sont générés à partir de `tools/drawings.py` par
  `tools/make_sprites.py` : un fichier par pelage, animation et niveau.

## agents-cats : un chat par agent

Copie du mod `agents` de Herdr (la liste des agents de la barre latérale) où
chaque agent Claude Code a pour icône un chat. Chaque agent a son pelage, fixe
pour une même adresse de terminal ; ses sous-agents sont des chatons. Les
autres agents (Codex, etc.) gardent leur icône.

| État Herdr | Chat |
|---|---|
| `working` | s'occupe : ordinateur, crêpes, pelote, Rubik's cube, à tour de rôle |
| `blocked` (besoin de toi) | miaule |
| `done` | saute de joie |
| `idle` | assis ; endormi après 3 minutes sans activité (sauf l'agent affiché) |

Un chat occupé (un agent au travail, ou le chat d'usage pendant que Claude
consomme) change d'occupation toutes les 3 secondes environ, comme les chats de
bureau de we-always-need-cats quand Claude réfléchit : il tape sur son
ordinateur, fait sauter une crêpe, joue avec une pelote de laine, puis résout
un Rubik's cube. Chaque pelage commence le cycle par une occupation
différente : deux agents voisins ne font pas tous la même chose.

## toast-cats : les notifications d'agent

Herdr envoie une notification quand un agent a fini pendant que tu regardais
ailleurs, ou quand il a besoin de toi. Pour un agent Claude Code, elle prend
la forme des chats de we-always-need-cats : le chat de l'agent, du même pelage
que dans la liste, et sa bulle avec le projet et le nom de la tâche.

| Notification | Chat | Bulle |
|---|---|---|
| L'agent a fini | saute de joie | bordure verte, « a fini » |
| L'agent a besoin de toi | miaule | bordure orange, « a besoin de toi » |

Comme la notification d'origine, un clic affiche l'agent et la ferme, et elle
disparaît seule au bout de quelques secondes. Les autres notifications (chat
d'usage, Herdr) gardent leur apparence.

Le mod est choisi par la clé `"toast"` du layout `main-usage-cat`.

## claude-sessions : les sessions Claude

Le bouton `sessions` (tête de chat), sous Settings en bas de la barre
latérale, ou `ctrl-shift-j`, ouvre la liste de toutes les sessions Claude Code enregistrées
sur la machine (`~/.claude/projects`), de la plus récente à la plus ancienne.
Chaque ligne donne le titre de la session (le nom donné par `/rename`, sinon
le titre choisi par Claude Code, sinon la première demande), son projet, sa
branche, le nombre de demandes, la dernière demande et sa date.

- Taper filtre la liste (titre, projet, dossier, branche, demandes ; tous les
  mots doivent apparaître).
- Haut, bas, page haut, page bas pour choisir ; Entrée ou clic pour ouvrir ;
  Echap pour fermer.

| Session | Entrée ou clic |
|---|---|
| fermée | la reprend (`claude --resume <id>`) dans un nouvel onglet, dans l'espace Herdr qui a un terminal dans son dossier, sinon dans un nouvel espace |
| ouverte dans Herdr (étiquette « ouverte ») | affiche son agent |
| ouverte hors de Herdr (autre terminal, IDE) | rien : la reprendre ferait deux sessions sur le même historique |

Clic droit sur une session : un menu propose de la reprendre (ou de
l'afficher si elle est ouverte dans Herdr) et de la supprimer. Supprimer
demande confirmation (« Êtes-vous sûr de supprimer la session `<id>`
« titre » ? » ; Entrée confirme, Echap annule), puis met à la corbeille le
fichier de la session, son dossier (sous-agents) et ses dossiers
`~/.claude/file-history/<id>` et `~/.claude/session-env/<id>`. Sans `gio`, ils
sont supprimés définitivement. Une session ouverte ne peut pas être supprimée :
la fermer d'abord.

Les fichiers de session sont lus par `claude-sessions/sessions.py`. Ce qui en
est tiré est gardé dans `~/.cache/herdr-always-need-cats/sessions.json` : seul
un fichier modifié depuis est relu (la première ouverture prend quelques
secondes). Les sessions vides (ouvertes puis quittées sans demande) ne sont
pas listées.

Le raccourci est ajouté à `~/.config/herdr-app/keys.json` par `install.py`,
seulement s'il n'est pas déjà pris (sinon le script le signale). La liste
s'ouvre aussi par `herdr-app do mod.open --name claude-sessions`. Toute
modification de `keys.json` le rend personnel : Herdr n'y ajoute plus ses
nouveaux raccourcis par défaut lors de ses mises à jour.

## strip-cats : la bande des chats

Une bande de 128 px en bas de la fenêtre, au-dessus de la barre d'état, où
chaque agent est un chat qui se promène dans un décor. Le chat a le même
pelage que dans la liste des agents et les notifications. Une bulle dit
toujours ce qu'il fait, grâce aux hooks de Claude Code (voir plus bas) :
« écrit main.js », « lance : npm test », « attend ton accord ».

| Agent | Chat |
|---|---|
| travaille | trotte d'un point à l'autre ; à chaque pause, se met à son ordinateur (l'écran prend la couleur de l'action : écrire, lire, commande, web, sous-agent) ou, quand Claude réfléchit, fait sauter une crêpe |
| au repos | flâne, puis s'endort après 3 minutes sans changement dans son onglet |
| t'attend (question, autorisation, plan, erreur) | sautille avec un « ? » (plus vite après 2 minutes) ; bulle orange qui dit pourquoi et depuis combien de temps |
| a fini sans que tu regardes | saute de joie, bulle verte « Fini ! On continue ? » ; une fois regardé, miaule « on continue ? » jusqu'à ce que tu le relances |

- Les sous-agents d'une session sont des chatons assis à côté de lui ; un
  nouvel agent arrive en courant depuis le bord de la bande.
- Survol : son pelage et son nom. Clic : son agent.
- Clic droit sur un chat, ou `alt-shift-p` (l'agent actif) : le menu. On y
  choisit son pelage (gardé pour son terminal, et repris par la liste des
  agents, les notifications et l'en-tête de son volet), le décor (salon,
  cuisine, bureau, jardin, toits la nuit, grenier ; « Mélanger », par défaut,
  en change toutes les 20 minutes ; « Aucun » les enlève), quand le petit chat
  vient te prévenir et si le chat bondit dans son volet.

**Le petit chat messager.** Quand un agent se met à t'attendre ou finit, son
chat libère un petit chat qui court jusqu'au milieu de la fenêtre et s'y pose
avec une bulle. Un clic sur lui ou sa bulle ouvre l'agent ; × le renvoie. Il
revient toutes les 5 minutes tant que l'agent t'attend, et repart tout seul
quand l'agent reprend le travail.

**Donner des fichiers à un agent.** Déposer des fichiers (depuis le
gestionnaire de fichiers) sur son chat, ou sur l'en-tête de son volet : le
chat les mange, et ils arrivent dans le prompt de l'agent en mentions `@`
(des pièces jointes pour Claude Code), sans valider. Un nom avec espaces ou
accents passe par un lien dans `~/.cache/herdr-always-need-cats/drop/` ; un
agent sur une autre machine reçoit d'abord le fichier (`hc put`). Le collage
passe par le presse-papiers : il faut `wl-copy` (paquet `wl-clipboard`, sous
Wayland) ou `xclip` (X11) ; le presse-papiers est remis comme avant s'il
contenait du texte.

**Démonstration** : `herdr-app do strip-cats.demo` (a fini) ou
`herdr-app do strip-cats.demo-blocked` (t'attend) joue la scène sur l'agent
actif pendant 30 secondes ; `herdr-app do strip-cats.demo-eat`, le repas.

### Les hooks : ce que fait chaque session

`hook.py` est déclaré dans `~/.claude/settings.json` pour les événements de
Claude Code (outils, demandes, notifications, fin, sous-agents), **à côté**
des hooks déjà en place : ceux de we-always-need-cats continuent de tout
recevoir. Dans un terminal Herdr, il écrit ce que fait la session dans
`~/.cache/herdr-always-need-cats/sessions/<session>.json`, que la bande relit
dès qu'il change ; hors de Herdr, il ne fait rien. Sans les hooks, les chats
marchent quand même, avec ce que Herdr sait de l'agent (travaille, attend, a
fini). Les textes suivent `lang` de `config.json`.

## pane-cats : l'en-tête des volets

L'en-tête de chaque volet est celui de Herdr (programme, dossier, état,
boutons au survol), avec un chat : quand l'agent t'attend ou a fini,
l'en-tête se teinte (orange, vert) et son chat y sautille avec sa bulle. Cela
se coupe dans le menu de la bande (« Bondir dans son volet »).

## Réglages : `config.json`

`install.py` crée `config.json` à partir de `config.example.json`. Ce fichier
est propre à la machine et ignoré par git : le modifier ne bloque pas les
mises à jour.

| Clé | Défaut | Rôle |
|---|---|---|
| `lang` | `fr` | langue des chats, des notifications, de la liste des sessions, de la bande, des hooks et de la status line : `fr` ou `en` |
| `coat` | `ginger` | pelage du chat d'usage : `ginger`, `grey`, `black`, `cream`, `brown` ou `blue` |
| `warn` | `50` | usage (%) à partir duquel la jauge passe au jaune |
| `alert` | `80` | usage (%) à partir duquel le chat miaule |
| `critical` | `95` | usage (%) à partir duquel le chat panique |
| `statusline` | `true` | `false` : la status line enregistre les chiffres sans rien afficher |

Les mods lisent ce fichier à leur démarrage : changer de layout et revenir
(`ctrl-shift-l`), ou relancer Herdr, après une modification.

## Installation

```bash
git clone https://github.com/MmeOokamy/herdr-always-need-cats.git
cd herdr-always-need-cats
python3 install.py
```

Prérequis : Herdr, Python 3.9+. Pillow n'est utile que pour régénérer les
images (`pip install pillow`) : elles sont déjà dans le dépôt.

Le script :

1. crée `config.json` à partir de `config.example.json` s'il n'existe pas ;
2. génère les images si elles manquent ;
3. crée les liens `~/.config/herdr-app/mods/usage-cat`, `agents-cats`,
   `toast-cats`, `claude-sessions`, `sessions-footer`, `strip-cats` et
   `pane-cats` vers les dossiers du clone, et les vérifie
   (`herdr-app check`) ;
4. crée le layout `main-usage-cat`, copie du layout `main` de Herdr (qui
   n'est pas modifiable) : le bloc du chat d'usage (112 px de haut) entre
   `spaces` et `agents`, la liste des agents remplacée par `agents-cats`, les
   notifications confiées à `toast-cats`, le pied de la barre latérale
   remplacé par `sessions-footer` (Settings, `sessions`, Add machine), la
   bande des chats (`strip-cats`, 128 px) au-dessus de la barre d'état,
   l'en-tête des volets remplacé par `pane-cats` ; et l'affiche ;
5. lie `ctrl-shift-j` à la liste des sessions Claude et `alt-shift-p` au
   menu de la bande dans `~/.config/herdr-app/keys.json`, si les touches sont
   libres ;
6. déclare `hook.py` comme hook de Claude Code (`~/.claude/settings.json`),
   à côté des hooks déjà en place ;
7. déclare `statusline.py` comme status line de Claude Code
   (`~/.claude/settings.json`), sauf si une autre status line est déjà en
   place : elle est gardée, et le script le signale. `--statusline` la
   remplace.

Le script peut être relancé sans risque. `ctrl-shift-l` fait passer d'un
layout à l'autre.

Herdr ne recharge un mod qu'au changement de layout. Après une modification
d'un mod, changer de layout et revenir, ou relancer `python3 install.py`.

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
`install.py` est relancé : il applique les changements de layout et recharge
les mods.

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

Revient au layout `main`, supprime `main-usage-cat` et les liens des mods,
retire les raccourcis `ctrl-shift-j` et `alt-shift-p` s'ils mènent toujours à
la liste des sessions et au menu de la bande, retire `hook.py` des hooks de
Claude Code (les autres hooks restent), et retire la status line de Claude Code si c'est celle du projet.

## Fichiers

| Chemin | Rôle |
|---|---|
| `usage-cat/` | le chat d'usage (mod gpui-kit et ses images) |
| `agents-cats/` | la liste des agents avec les chats (mod et images) |
| `toast-cats/` | les notifications avec les chats (mod) |
| `claude-sessions/` | la liste des sessions Claude (mod, et `sessions.py` qui lit les sessions) |
| `sessions-footer/` | le pied de la barre latérale avec le bouton `sessions` (mod et icône) |
| `strip-cats/` | la bande des chats, le menu et le petit chat (mod), ses images (`img/`, GIF) et ses décors (`scenes/`) |
| `strip-cats/tools/` | `make_scenes.py` redessine les décors ; `make_sprites.py` et `make_think.py` les GIF, à partir d'un clone de we-always-need-cats (Pillow, PyQt6) |
| `pane-cats/` | l'en-tête des volets avec le chat (mod et icônes) |
| `hook.py` | hook de Claude Code, écrit ce que fait chaque session pour la bande |
| `tools/drawings.py` | dessins et couleurs des chats (texte, un caractère par pixel) |
| `tools/make_sprites.py` | génération des images (Pillow) |
| `statusline.py` | status line de Claude Code, écrit les chiffres d'usage |
| `updates.py` | vérification et mise à jour depuis les releases GitHub |
| `config.example.json` | réglages par défaut, copiés en `config.json` (local) |
| `install.py` | installation dans Herdr et Claude Code |

## Limites

- `main-usage-cat` est une copie : les évolutions du layout `main` livrées
  par les mises à jour de Herdr n'y arrivent pas. Pour repartir d'une copie à
  jour : désinstaller puis réinstaller.
- `agents-cats` et `toast-cats` partent des mods `agents` et `toast` de Herdr
  0.1.15, gardés pour comparaison (`upstream-*.js.txt`). Ils ne suivent pas
  leurs évolutions : pour une nouvelle version de Herdr, comparer ces fichiers
  aux nouveaux `~/.config/herdr-app/mods/agents/main.js` et `toast/main.js`,
  puis reporter les modifications (marquées `agents-cats` dans le premier).
- `sessions-footer` reprend le pied de barre latérale du mod `workspace-chrome`
  de Herdr 0.1.15 (Settings, Add machine) : ses évolutions n'y arrivent pas
  non plus.
- `pane-cats` reprend le mod `pane` de Herdr 0.1.15 : ses évolutions n'y
  arrivent pas non plus.
- Les images de la bande (`strip-cats/img/`, GIF) ne sont pas celles des
  autres mods (`sprites/`, WebP générés par `tools/make_sprites.py`) : elles
  sont tirées des dessins de we-always-need-cats et se régénèrent avec
  `strip-cats/tools/`.
- Donner des fichiers à un agent demande `wl-copy` ou `xclip`.
- Claude Code n'a qu'une status line. Le fichier
  `~/.cache/usage-cat/state.json` a le même format que celui de
  [we-always-need-cats](https://github.com/MmeOokamy/we-always-need-cats)
  (chats de bureau) : si ce projet est aussi installé, sa status line
  alimente aussi le chat de Herdr, et `install.py` la garde.

## Licence

MIT (voir `LICENSE`), sauf `agents-cats/main.js`, `toast-cats/main.js`,
`sessions-footer/main.js`, `pane-cats/main.js` et les fichiers
`upstream-*.js.txt` : ils reprennent les mods `agents`, `toast`,
`workspace-chrome` et `pane` de Herdr, sous licence Apache 2.0 (`agents-cats/LICENSE-herdr.txt`), avec les
modifications décrites ci-dessus.

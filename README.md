# herdr-always-need-cats

English | [Français](README.fr.md)

Pixel art cats in the Herdr app (`~/.config/herdr-app`):

- a usage cat in the sidebar;
- one cat per Claude Code agent in the agents list;
- agent notifications shaped like a cat with its speech bubble.

The project stands on its own: it holds its drawings, its status line and its
settings.

## usage-cat: the usage cat

A cat in the Herdr sidebar, between Spaces and Agents. It watches the usage
limits of the Claude Code account:

- under the cat, thick gauge: the session (5-hour window); thin gauge: the
  week (7 days);
- on the right: the percentage of each window and the time of its next reset
  (hidden when the sidebar is collapsed).

| Usage (session or week) | What the cat does |
|---|---|
| Below 50% | Sits, green gauge; busy while Claude is (see below) |
| 50% and more | Same, yellow gauge |
| 80% and more | Meows, orange exclamation mark, Herdr notification |
| 95% and more | Meows faster, in red, Herdr notification |
| 100% | Sleeps until the reset |
| Reset of a nearly reached limit | Jumps for joy for 30 seconds |

It also tells when the project has an update (see [Updates](#updates)).

### How it works

- The figures come from `~/.cache/usage-cat/state.json`, written by
  `statusline.py`, the Claude Code status line set up by `install.py`. The
  mod reads this file every 2 seconds.
- Language, coat and thresholds are read from `config.json` when the mod
  starts.
- The animations are animated WebP images, played natively by Herdr (no
  redraw on a timer). `tools/make_sprites.py` generates them from
  `tools/drawings.py`: one file per coat, animation and level.

## agents-cats: one cat per agent

A copy of the Herdr `agents` mod (the agents list of the sidebar) where each
Claude Code agent has a cat as its icon. Each agent has its own coat, the
same for a given terminal address; its subagents are kittens. Other agents
(Codex, etc.) keep their icon.

| Herdr state | Cat |
|---|---|
| `working` | busy: laptop, crepes, yarn, Rubik's cube, in turn |
| `blocked` (needs you) | meows |
| `done` | jumps for joy |
| `idle` | sits; falls asleep after 3 minutes without activity (except the agent on screen) |

A busy cat (an agent at work, or the usage cat while Claude uses the account)
takes turns, about 3 seconds each, as the desktop cats of we-always-need-cats
do while Claude thinks: it types on its laptop, flips a crepe, plays with a
ball of yarn, then solves a Rubik's cube. Each coat starts the cycle at
another turn, so that neighbouring agents do not all do the same thing.

## toast-cats: agent notifications

Herdr posts a notification when an agent finished while you were looking
elsewhere, or when it needs you. For a Claude Code agent, it takes the shape
of the we-always-need-cats cats: the agent's cat, with the same coat as in
the list, and its speech bubble with the project and the task name.

| Notification | Cat | Bubble |
|---|---|---|
| The agent finished | jumps for joy | green border, "done" |
| The agent needs you | meows | orange border, "needs you" |

As with the original notification, a click shows the agent and closes it,
and it goes away by itself after a few seconds. Other notifications (usage
cat, Herdr) keep their look.

The mod is chosen by the `"toast"` key of the `main-usage-cat` layout.

## Settings: `config.json`

`install.py` creates `config.json` from `config.example.json`. This file
belongs to the machine and is ignored by git: changing it does not block
updates.

| Key | Default | Meaning |
|---|---|---|
| `lang` | `fr` | language of the cats, notifications and status line: `fr` or `en` |
| `coat` | `ginger` | coat of the usage cat: `ginger`, `grey`, `black`, `cream`, `brown` or `blue` |
| `warn` | `50` | usage (%) from which the gauge turns yellow |
| `alert` | `80` | usage (%) from which the cat meows |
| `critical` | `95` | usage (%) from which the cat panics |
| `statusline` | `true` | `false`: the status line saves the figures without printing anything |

The mods read this file when they start: switch to another layout and back
(`ctrl-shift-l`), or restart Herdr, after a change.

## Install

```bash
git clone https://github.com/MmeOokamy/herdr-always-need-cats.git
cd herdr-always-need-cats
python3 install.py
```

Requirements: Herdr, Python 3.9+. Pillow is only needed to generate the
images again (`pip install pillow`): they are already in the repository.

The script:

1. creates `config.json` from `config.example.json` when it does not exist;
2. generates the images when they are missing;
3. links `~/.config/herdr-app/mods/usage-cat`, `agents-cats` and
   `toast-cats` to the folders of the clone, and checks them
   (`herdr-app check`);
4. creates the `main-usage-cat` layout, a copy of the Herdr `main` layout
   (which cannot be edited): the usage cat block (112 px high) between
   `spaces` and `agents`, the agents list replaced by `agents-cats`,
   notifications shown by `toast-cats`; and shows it;
5. sets `statusline.py` as the Claude Code status line
   (`~/.claude/settings.json`), unless another status line is already set:
   it is kept, and the script says so. `--statusline` replaces it.

The script can run again without harm. `ctrl-shift-l` switches layouts.

Herdr reloads a mod only when the layout changes. After editing a mod,
switch to another layout and back, or run `python3 install.py` again.

After editing `tools/drawings.py`:

```bash
python3 tools/make_sprites.py
```

## Updates

The project updates itself from the git clone it was installed with. Only
releases are offered: the `vX.Y.Z` tags published on GitHub. What is merged
on `main` between two releases waits for the next one.

- **In Herdr**: once a day, the usage cat checks for a new version. When
  there is one, it shows "Update X.Y.Z available" under the gauges (an "UPD"
  label under the cat when the sidebar is collapsed) and posts a
  notification. A click on the line, the label or the notification runs the
  update, then a notification tells the result.
- **In a terminal**:

  ```bash
  python3 updates.py           # check, then update if there is a new version
  python3 updates.py --check   # check only
  ```

An update never overwrites anything: it fast-forwards the clone to the latest
release (`git merge --ff-only`). With modified tracked files or local
commits, it stops and the cat shows "Update blocked": update by hand then.
After the update, `install.py` runs again: it applies layout changes and
reloads the mods.

The state of the last check is kept in
`~/.cache/herdr-always-need-cats/updates.json`.

### Publishing a release

From an up to date `main`:

```bash
git tag -a v1.1.0 -m "v1.1.0"
git push origin v1.1.0
```

Then create the release on GitHub from the tag (Releases, Draft a new
release). Installations see it at their next check.

## Uninstall

```bash
python3 install.py --uninstall
```

Goes back to the `main` layout, deletes `main-usage-cat` and the mod links,
and removes the Claude Code status line when it is the project's one.

## Files

| Path | Role |
|---|---|
| `usage-cat/` | the usage cat (gpui-kit mod and its images) |
| `agents-cats/` | the agents list with the cats (mod and images) |
| `toast-cats/` | the notifications with the cats (mod) |
| `tools/drawings.py` | drawings and colors of the cats (text, one character per pixel) |
| `tools/make_sprites.py` | image generation (Pillow) |
| `statusline.py` | Claude Code status line, writes the usage figures |
| `updates.py` | checks and updates from the GitHub releases |
| `config.example.json` | default settings, copied to `config.json` (local) |
| `install.py` | install into Herdr and Claude Code |

## Limits

- `main-usage-cat` is a copy: changes to the `main` layout shipped by Herdr
  updates do not reach it. To start again from an up to date copy: uninstall,
  then install.
- `agents-cats` and `toast-cats` start from the Herdr 0.1.15 `agents` and
  `toast` mods, kept for comparison (`upstream-*.js.txt`). They do not follow
  their changes: for a new Herdr version, compare these files with the new
  `~/.config/herdr-app/mods/agents/main.js` and `toast/main.js`, then carry
  the changes over (marked `agents-cats` in the first one).
- Claude Code has a single status line. The file
  `~/.cache/usage-cat/state.json` has the same format as the one of
  [we-always-need-cats](https://github.com/MmeOokamy/we-always-need-cats)
  (desktop cats): when that project is installed too, its status line feeds
  the Herdr cat as well, and `install.py` keeps it.

## License

MIT (see `LICENSE`), except `agents-cats/main.js`, `toast-cats/main.js` and
the `upstream-*.js.txt` files: they build on the Herdr `agents` and `toast`
mods, under the Apache 2.0 license (`agents-cats/LICENSE-herdr.txt`), with
the changes described above.

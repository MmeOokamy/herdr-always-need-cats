# herdr-always-need-cats

English | [Français](README.fr.md)

Pixel art cats in the Herdr app (`~/.config/herdr-app`):

- a usage cat in the sidebar;
- one cat per Claude Code agent in the agents list;
- agent notifications shaped like a cat with its speech bubble;
- the list of every Claude Code session, to resume one;
- a strip at the bottom of the window where each agent is a cat walking
  around, with a little messenger cat when it waits for you or is done;
- the pane headers, where the cat hops.

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

## claude-sessions: the Claude sessions

The `sessions` button (a cat head), under Settings at the bottom of the
sidebar, or `ctrl-shift-j`, opens the list of every Claude Code session saved on the
machine (`~/.claude/projects`), newest first. Each row shows the session's
title (the name given with `/rename`, else the title Claude Code picked, else
the first prompt), its project, its branch, the number of prompts, the last
prompt and its date.

- Typing filters the list (title, project, folder, branch, prompts; every
  word must appear).
- Up, down, page up, page down to pick; Enter or click to open; Esc to
  close.

| Session | Enter or click |
|---|---|
| closed | resumes it (`claude --resume <id>`) in a new tab, in the Herdr space that has a terminal in its folder, else in a new space |
| open in Herdr ("open" label) | shows its agent |
| open outside Herdr (another terminal, an IDE) | nothing: resuming it would make two sessions on the same history |

Right-click a session: a menu offers to resume it (or to show it when it is
open in Herdr) and to delete it. Deleting asks first ("Are you sure you want
to delete the session `<id>` "title"?"; Enter confirms, Esc cancels), then
moves to the trash the session file, its folder (sub-agents) and its
`~/.claude/file-history/<id>` and `~/.claude/session-env/<id>` folders.
Without `gio`, they are deleted for good. An open session cannot be deleted:
close it first.

Session files are read by `claude-sessions/sessions.py`. What it takes from
them is kept in `~/.cache/herdr-always-need-cats/sessions.json`: only a file
changed since then is read again (the first opening takes a few seconds).
Empty sessions (opened then left without a prompt) are not listed.

`install.py` adds the shortcut to `~/.config/herdr-app/keys.json`, only when
the key is free (otherwise the script says so). The list also opens with
`herdr-app do mod.open --name claude-sessions`. Any edit to `keys.json` makes
it personal: Herdr no longer adds its new default shortcuts to it when it
updates.

## strip-cats: the cats strip

A 128 px strip at the bottom of the window, above the status bar, where each
agent is a cat walking around a scene. The cat has the same coat as in the
agents list and the notifications. A speech bubble always says what it does,
thanks to the Claude Code hooks (see below): "writes main.js",
"runs: npm test", "waits for your approval".

| Agent | Cat |
|---|---|
| working | trots from one spot to another; at each stop, sits at its computer (the screen takes the color of the action: write, read, command, web, sub-agent) or, while Claude thinks, flips a crepe |
| idle | wanders, then falls asleep after 3 minutes without change in its tab |
| waits for you (question, permission, plan, error) | hops with a "?" (faster after 2 minutes); orange bubble saying why and for how long |
| done while you were not looking | jumps for joy, green bubble "Done! Shall we go on?"; once seen, meows "shall we go on?" until you start it again |

- The sub-agents of a session are kittens sitting next to it; a new agent
  comes running from the edge of the strip.
- Hover: its coat and name. Click: its agent.
- Right-click a cat, or `alt-shift-p` (the active agent): the menu. It picks
  its coat (kept for its terminal, and used by the agents list, the
  notifications and its pane header too), the scene (living room, kitchen,
  office, garden, rooftops at night, attic; "Shuffle", the default, changes
  it every 20 minutes; "None" removes it), when the little cat comes to tell
  you, and whether the cat hops in its pane.

**The little messenger cat.** When an agent starts waiting for you or is
done, its cat sends a little cat running up to the middle of the window,
where it sits with a bubble. A click on it or its bubble opens the agent;
x sends it away. It comes back every 5 minutes while the agent waits for
you, and leaves by itself when the agent goes back to work.

**Giving files to an agent.** Drop files (from the file manager) on its cat,
or on its pane header: the cat eats them, and they land in the agent's prompt
as `@` mentions (attachments for Claude Code), without sending. A name with
spaces or accents goes through a link in
`~/.cache/herdr-always-need-cats/drop/`; an agent on another machine first
gets the file (`hc put`). Pasting goes through the clipboard: it needs
`wl-copy` (package `wl-clipboard`, on Wayland) or `xclip` (X11); the
clipboard is put back as it was when it held text.

**Demo**: `herdr-app do strip-cats.demo` (done) or
`herdr-app do strip-cats.demo-blocked` (waits for you) plays the scene on the
active agent for 30 seconds; `herdr-app do strip-cats.demo-eat`, the meal.

### The hooks: what each session does

`hook.py` is declared in `~/.claude/settings.json` for the Claude Code events
(tools, prompts, notifications, stop, sub-agents), **next to** the hooks
already there: the we-always-need-cats ones keep receiving everything. In a
Herdr terminal, it writes what the session does to
`~/.cache/herdr-always-need-cats/sessions/<session>.json`, which the strip
reads again as soon as it changes; outside Herdr, it does nothing. Without
the hooks, the cats still work, with what Herdr knows about the agent
(working, waiting, done). The texts follow `lang` in `config.json`.

## pane-cats: the pane headers

Each pane header is the Herdr one (program, folder, status, buttons on
hover), with a cat: when the agent waits for you or is done, the header gets
tinted (orange, green) and its cat hops there with its bubble. This can be
turned off in the strip menu ("Hop in its pane").

## Settings: `config.json`

`install.py` creates `config.json` from `config.example.json`. This file
belongs to the machine and is ignored by git: changing it does not block
updates.

| Key | Default | Meaning |
|---|---|---|
| `lang` | `fr` | language of the cats, notifications, sessions list, strip, hooks and status line: `fr` or `en` |
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
3. links `~/.config/herdr-app/mods/usage-cat`, `agents-cats`, `toast-cats`,
   `claude-sessions`, `sessions-footer`, `strip-cats` and `pane-cats` to the
   folders of the clone, and checks them
   (`herdr-app check`);
4. creates the `main-usage-cat` layout, a copy of the Herdr `main` layout
   (which cannot be edited): the usage cat block (112 px high) between
   `spaces` and `agents`, the agents list replaced by `agents-cats`,
   notifications shown by `toast-cats`, the sidebar footer replaced by
   `sessions-footer` (Settings, `sessions`, Add machine), the cats strip
   (`strip-cats`, 128 px) above the status bar, the pane headers replaced by
   `pane-cats`; and shows it;
5. binds `ctrl-shift-j` to the Claude sessions list and `alt-shift-p` to the
   strip menu in `~/.config/herdr-app/keys.json`, when the keys are free;
6. declares `hook.py` as a Claude Code hook (`~/.claude/settings.json`), next
   to the hooks already there;
7. sets `statusline.py` as the Claude Code status line
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
removes the `ctrl-shift-j` and `alt-shift-p` shortcuts when they still open
the sessions list and the strip menu, removes `hook.py` from the Claude Code
hooks (the other hooks stay), and removes the Claude Code status line when it is the project's one.

## Files

| Path | Role |
|---|---|
| `usage-cat/` | the usage cat (gpui-kit mod and its images) |
| `agents-cats/` | the agents list with the cats (mod and images) |
| `toast-cats/` | the notifications with the cats (mod) |
| `claude-sessions/` | the Claude sessions list (mod, and `sessions.py` which reads the sessions) |
| `sessions-footer/` | the sidebar footer with the `sessions` button (mod and icon) |
| `strip-cats/` | the cats strip, the menu and the little cat (mod), its images (`img/`, GIF) and its scenes (`scenes/`) |
| `strip-cats/tools/` | `make_scenes.py` draws the scenes again; `make_sprites.py` and `make_think.py` the GIFs, from a we-always-need-cats clone (Pillow, PyQt6) |
| `pane-cats/` | the pane headers with the cat (mod and icons) |
| `hook.py` | Claude Code hook, writes what each session does for the strip |
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
- `sessions-footer` builds on the sidebar footer of the Herdr 0.1.15
  `workspace-chrome` mod (Settings, Add machine): its changes do not reach it
  either.
- `pane-cats` builds on the Herdr 0.1.15 `pane` mod: its changes do not
  reach it either.
- The strip images (`strip-cats/img/`, GIF) are not the ones of the other
  mods (`sprites/`, WebP generated by `tools/make_sprites.py`): they are made
  from the we-always-need-cats drawings and are generated again with
  `strip-cats/tools/`.
- Giving files to an agent needs `wl-copy` or `xclip`.
- Claude Code has a single status line. The file
  `~/.cache/usage-cat/state.json` has the same format as the one of
  [we-always-need-cats](https://github.com/MmeOokamy/we-always-need-cats)
  (desktop cats): when that project is installed too, its status line feeds
  the Herdr cat as well, and `install.py` keeps it.

## License

MIT (see `LICENSE`), except `agents-cats/main.js`, `toast-cats/main.js`,
`sessions-footer/main.js`, `pane-cats/main.js` and the `upstream-*.js.txt`
files: they build on the Herdr `agents`, `toast`, `workspace-chrome` and
`pane` mods, under the Apache 2.0 license (`agents-cats/LICENSE-herdr.txt`), with
the changes described above.

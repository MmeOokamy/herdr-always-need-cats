// strip-cats: a strip of cats for herdr-always-need-cats. Coat shared with agents-cats and
// toast-cats (picked from the terminal's address, or in the menu: shared "strip-cats".terminals),
// texts in French or English (config.json), this project's hooks (hook.py,
// ~/.cache/herdr-always-need-cats/sessions), clipboard through wl-copy
// or xclip.
//
// A strip at the bottom of the window where each agent is a pixel-art cat wandering around
// a scene (living room, kitchen, office, garden, rooftops at night, attic), with a bubble that
// always says what it is doing.
//
// - Working: it trots from one spot to another and, at each stop, sits at its computer (the screen
//   takes the color of the action) or, when Claude is thinking, flips a pancake.
// - Idle: it strolls, then falls asleep after 3 minutes without any change in its tab.
// - Waiting for you: it hops with a "?", its orange bubble says why and for how long.
//   It releases a little cat that runs to the middle of the screen to tell you (and comes back every
//   5 minutes while it waits), and it jumps into its pane's header ("cats-pane" mod).
// - Finished: it jumps for joy, its green bubble asks "Shall we go on?", and the little cat goes up too.
//   A click on the little cat or its bubble opens the agent's pane.
// - Its subagents are kittens sitting next to it; a new agent comes running in.
// Click: its agent. Right click (or alt-shift-p): coat, scene, and what pops up or not.
// Files dropped on a cat (or on its agent's pane header, through shared "strip-cats.drop"):
// pasted into the agent's prompt as @ mentions (attachments for Claude Code), without submitting.
// A name with spaces or accents goes through a link in ~/.cache/herdr-always-need-cats/drop; an agent on
// another machine first receives the file (hc put). The clipboard is used to paste, then restored.
//
// This mod has three roles: the strip (layout), the menu (dialog, props.picker) and the little cat
// (window, props.alert: phase "run", the run upward, then "perch", sitting at the top). Shared state:
//   "strip-cats"        { terminals: { <address>: <coat> } }: coats picked in the menu, also read
//                       by agents-cats, toast-cats and pane-cats
//   "strip-cats.live"   { <terminal>: { mood, text, since } }, for pane-cats
//   "strip-cats.scene"  "shuffle" | a scene id | "off"
//   "strip-cats.alert"  { blocked, done }: the little cat comes to warn you
//   "strip-cats.header" jumps into the pane header
// Cat drawings: we-always-need-cats, by MmeOokamy (MIT).
// Scenes: drawn by tools/make_scenes.py.
import { View, div, image } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { agents, terminals, spaces, theme, settings, run, props, shared, setShared, openOverlay, closeOverlay, nextCommand, home, watchFolder, exec, hc, notify, layout, appHome, readTextFile } from "herdr";
import * as fs from "fs/promises";

const MOD = "strip-cats";
const KEY = "strip-cats";
const LIVE_KEY = "strip-cats.live";
const SCENE_KEY = "strip-cats.scene";
const ALERT_KEY = "strip-cats.alert";
const HEADER_KEY = "strip-cats.header";
const IMG = "mods/strip-cats/img";
const DROP_KEY = "strip-cats.drop";
// The meal: files fall into its mouth (FALL ms, staggered), it chews until CHEW, then is happy until FULL.
const MEAL = { fall: 520, stagger: 170, chew: 1900, full: 3200, mouth: 47, papers: 3 };

const COATS = ["ginger", "grey", "black", "cream", "brown", "blue"];
const KITTEN_COATS = ["pink", "mint", "lavender", "sky", "lemon", "coral"];
const ACTIVITIES = ["think", "write", "read", "shell", "web", "agent"];

const SCENES = ["salon", "cuisine", "bureau", "jardin", "toits", "grenier"].map((id) => ({ id }));

// Texts, according to "lang" in config.json.
const TEXTS = {
  fr: {
    coats: { ginger: "Roux", grey: "Gris", black: "Noir", cream: "Crème", brown: "Brun", blue: "Bleu" },
    scenes: { salon: "Salon", cuisine: "Cuisine", bureau: "Bureau", jardin: "Jardin", toits: "Toits, la nuit", grenier: "Grenier" },
    works: "travaille", needsYou: "a besoin de toi", doneAsk: "Fini ! On continue ?", goOn: "on continue ?",
    sleeps: "dort", idle: "au repos", min: (n) => `${n} min`,
    files: (n) => `${n} fichier${n > 1 ? "s" : ""}`, eating: (f) => `miam… ${f}`, ate: (f, n) => `${f} avalé${n > 1 ? "s" : ""} !`,
    empty: "Pas encore d'agent. Chaque agent que tu lances arrive ici en chat.",
    notSent: "Fichiers non transmis", noClipboard: "ni wl-copy ni xclip : installer wl-clipboard (ou xclip)",
    linkFailed: (p) => `lien impossible pour ${p}`, sendFailed: (p) => `envoi impossible : ${p}`,
    pickTitle: "Choisir un chat", pickFor: (tag, coat) => `pour ${tag ?? "cet agent"} · maintenant ${coat ?? "?"}`,
    esc: "Échap", scene: "Décor", shuffle: "Mélanger", none: "Aucun",
    alertRow: "Le petit chat vient me dire", alertBlocked: "quand il t'attend", alertDone: "quand il a fini",
    headerRow: "Bondir dans son volet", yes: "Oui", no: "Non", coat: "Pelage",
  },
  en: {
    coats: { ginger: "Ginger", grey: "Grey", black: "Black", cream: "Cream", brown: "Brown", blue: "Blue" },
    scenes: { salon: "Living room", cuisine: "Kitchen", bureau: "Office", jardin: "Garden", toits: "Rooftops, at night", grenier: "Attic" },
    works: "works", needsYou: "needs you", doneAsk: "Done! Shall we go on?", goOn: "shall we go on?",
    sleeps: "sleeps", idle: "resting", min: (n) => `${n} min`,
    files: (n) => `${n} file${n > 1 ? "s" : ""}`, eating: (f) => `yum… ${f}`, ate: (f) => `${f} eaten!`,
    empty: "No agent yet. Every agent you start comes here as a cat.",
    notSent: "Files not sent", noClipboard: "neither wl-copy nor xclip: install wl-clipboard (or xclip)",
    linkFailed: (p) => `cannot link ${p}`, sendFailed: (p) => `cannot send ${p}`,
    pickTitle: "Pick a cat", pickFor: (tag, coat) => `for ${tag ?? "this agent"} · now ${coat ?? "?"}`,
    esc: "Esc", scene: "Scene", shuffle: "Shuffle", none: "None",
    alertRow: "The little cat tells me", alertBlocked: "when it waits for you", alertDone: "when it is done",
    headerRow: "Hop in its pane", yes: "Yes", no: "No", coat: "Coat",
  },
};
const SCENE_W = 3840, SCENE_H = 114;
const SHUFFLE_MS = 20 * 60 * 1000;
const SCENE_DIM = 0.3;

const SLOT = 128;
const CAT_W = 66, CAT_H = 75;
const KIT_W = 44, KIT_H = 36;
const MAX_KITTENS = 3;
const LABEL_H = 18;
const BUBBLE_H = 20;
const FEET = 24;
const SPEED = { working: 80, idle: 38 };
const SLEEP_AFTER = 3 * 60 * 1000;
const SETTLE = 5000;
const REALERT = 5 * 60 * 1000; // still waiting: the cat window comes back
const DEMO_MS = 30000;
// The little cat: its size, its run (ms) and where it perches (fraction of the window height: the middle).
const KIT = { w: 40, h: 45, run: 1200, perch: 0.5, lane: 80, statusbar: 28 };
const perchY = (h) => Math.round(h * KIT.perch - KIT.h / 2);
const INK = "#2B2230", PAPER = "#FFFDF5";
const EDGE = { blocked: "#E8590C", done: "#2F9E44", finished: "#2F9E44" };

const alpha = (c, a) => (typeof c === "string" && /^#[0-9a-f]{6}$/i.test(c) ? c + a : c);
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const rand = (lo, hi) => lo + Math.random() * (hi - lo);
const zoom = () => (Number(settings()?.zoom) > 0 ? Number(settings().zoom) : 1);
const on = (key) => shared(key) !== false; // yes/no settings, yes by default
const alertOn = (kind) => {
  const a = shared(ALERT_KEY);
  return !(a && typeof a === "object" && a[kind === "blocked" ? "blocked" : "done"] === false);
};
const minutes = (ms) => Math.floor(ms / 60000);

// ---- scene ----------------------------------------------------------------------

const sceneChoice = () => {
  const v = shared(SCENE_KEY);
  return v === "off" || SCENES.some((s) => s.id === v) ? v : "shuffle";
};

function sceneNow(now = Date.now()) {
  const c = sceneChoice();
  if (c === "off") return null;
  return c === "shuffle" ? SCENES[Math.floor(now / SHUFFLE_MS) % SCENES.length] : SCENES.find((s) => s.id === c);
}

// ---- which cat is who ------------------------------------------------------------
// Like agents-cats and toast-cats: a coat derived from the terminal's address, unless it was
// picked in the menu.

function savedPicks() {
  const s = shared(KEY);
  return s && typeof s === "object" && s.terminals && typeof s.terminals === "object" ? s.terminals : {};
}

function savePicks(update) {
  const next = { ...savedPicks(), ...update };
  const keys = Object.keys(next);
  for (let i = 0; i < keys.length - 300; i++) delete next[keys[i]];
  setShared(KEY, { ...(shared(KEY) ?? {}), terminals: next });
}

function addressCoat(address) {
  let h = 0;
  for (const c of address) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return COATS[h % COATS.length];
}

function hash(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

const kittenCoat = (type) => KITTEN_COATS[hash(type || "agent") % KITTEN_COATS.length];

function assign(list) {
  const saved = savedPicks();
  const coats = {};
  for (const a of list) coats[a.address] = COATS.includes(saved[a.address]) ? saved[a.address] : addressCoat(a.address);
  return { coats };
}

// The sidebar, left of the strip (collapsed to a rail or not): where the little cat starts from.
function findSidebar(node) {
  if (node?.id === "sidebar") return node;
  for (const child of node?.children ?? []) {
    const found = findSidebar(child);
    if (found) return found;
  }
  return null;
}

function sidebarWidth() {
  const node = findSidebar(layout());
  return !node || node.hidden ? 0 : Number(node.size?.px) || 268;
}

function tabsById() {
  const out = {};
  for (const s of spaces()) for (const t of s.tabs) out[t.id] = { ...t, space_name: s.name };
  return out;
}

function labelsByAddress() {
  const out = {};
  for (const t of terminals()) if (t.labels) out[t.address] = t.labels;
  return out;
}

function tagOf(a, tabs, labels) {
  const l = labels[a.address];
  if (l?.support) return l.support;
  if (l?.fix) return l.fix;
  const t = tabs[a.tab];
  if (t?.named && t.name !== a.app && t.name !== "claude") return t.name;
  return a.space_name || a.tab_name || a.address;
}

// The cat's mood. "finished": Herdr reports it as idle (you have looked), but the session finished
// its work and waits for what comes next: it still asks to be restarted.
function moodOf(a, tabs, now, s) {
  if (a.status === "blocked") return "blocked";
  if (a.status === "done") return "done";
  if (a.status === "working") return "working";
  if (s?.state === "done") return "finished";
  const changed = tabs[a.tab]?.changed_at;
  return !changed || now - changed > SLEEP_AFTER ? "sleep" : "idle";
}

// What the bubble says.
function saysOf(T, mood, s, since, now) {
  const wait = now - since >= 60000 ? ` · ${T.min(minutes(now - since))}` : "";
  if (mood === "working") return s?.state === "work" && s.text ? s.text : T.works;
  if (mood === "blocked") return (s?.state === "question" && s.text ? s.text : T.needsYou) + wait;
  if (mood === "done") return T.doneAsk;
  if (mood === "finished") return T.goOn;
  return mood === "sleep" ? T.sleeps : T.idle;
}

// ---- dropped files ---------------------------------------------------------------

// A name that an @ mention does not split: no spaces, accents or quotes.
const plain = (path) => /^[A-Za-z0-9._\/+-]+$/.test(path);
const safeName = (name) => name.normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^A-Za-z0-9._+-]+/g, "_") || "fichier";

// The @ mentions for these files, ready for agent `address` (copied over if it is on another machine).
async function mentionsFor(T, address, paths) {
  const remote = String(address).includes("/");
  const dir = `${home()}/.cache/herdr-always-need-cats/drop/${Date.now().toString(36)}`;
  const out = [];
  for (const path of paths) {
    let here = path;
    if (remote || !plain(path)) {
      await exec("mkdir", ["-p", dir]);
      here = `${dir}/${safeName(path.split("/").pop())}`;
      if ((await exec("ln", ["-sfn", path, here])).code !== 0) throw new Error(T.linkFailed(path));
    }
    if (remote) {
      const r = await hc(["put", "--json", address, here]);
      if (r.code !== 0) throw new Error(r.stderr.trim() || T.sendFailed(path));
      here = JSON.parse(r.stdout).path;
    }
    out.push(`@${here}`);
  }
  return out.join(" ") + " ";
}

// The clipboard: wl-copy / wl-paste (Wayland), otherwise xclip (X11).
const CLIPBOARDS = [
  {
    check: ["wl-copy", ["--version"]],
    types: ["wl-paste", ["-l"]], read: ["wl-paste", ["-n"]],
    write: (text) => ["wl-copy", ["--", text]], clear: ["wl-copy", ["--clear"]],
  },
  {
    check: ["xclip", ["-version"]],
    types: ["xclip", ["-selection", "clipboard", "-o", "-t", "TARGETS"]], read: ["xclip", ["-selection", "clipboard", "-o"]],
    write: (text) => ["sh", ["-c", 'printf %s "$1" | xclip -selection clipboard', "sh", text]],
    clear: ["sh", ["-c", "printf '' | xclip -selection clipboard"]],
  },
];

async function clipboard(T) {
  for (const c of CLIPBOARDS) {
    const r = await exec(...c.check).catch(() => null);
    if (r && r.code === 0) return c;
  }
  throw new Error(T.noClipboard);
}

// Pastes the text into the agent's terminal without pressing Enter (Herdr's paste goes through
// the clipboard), then restores the clipboard as it was when it held text.
async function pasteInto(T, address, pane, text) {
  const c = await clipboard(T);
  const types = await exec(...c.types).catch(() => null);
  const hadText = types?.code === 0 && /text\/plain|UTF8_STRING|^TEXT$|^STRING$/m.test(types.stdout);
  const before = hadText ? (await exec(...c.read).catch(() => null))?.stdout ?? null : null;
  if ((await exec(...c.write(text))).code !== 0) throw new Error(`${c.write("")[0]} : échec`);
  if (pane) run("pane.focus", { pane }); else run("agent.focus", { terminal: address });
  await exec("sleep", ["0.15"]);
  run("terminal.paste");
  await exec("sleep", ["0.6"]);
  if (before != null) await exec(...c.write(before));
  else await exec(...c.clear);
}

// ---- the view ---------------------------------------------------------------------

export default class CatsStrip extends View {
  init(_p, cx) {
    const p = props() ?? {};
    this.role = p.alert ? "alert" : p.picker ? "picker" : "strip";
    this.lang = "fr";
    cx.spawn(async (cx) => {
      try {
        // The mod folder is a link to the clone: config.json sits next to it.
        const data = JSON.parse((await readTextFile(`${appHome()}/mods/${MOD}/../config.json`)) ?? "{}");
        const lang = String(data?.lang ?? "fr").toLowerCase();
        if (TEXTS[lang]) this.lang = lang;
      } catch {
        // no config: French
      }
      cx.notify();
    });
    if (this.role === "alert") return this.initAlert(cx);
    if (this.role === "picker") return;
    this.width = 900;
    this.height = 128;
    this.cats = {};
    this.sessions = {};
    this.since = {}; // address -> { mood, at }: since when it has been in this mood
    this.alerted = {}; // address -> { kind, at }: the last cat window opened
    this.hover = null;
    this.startedAt = Date.now();
    this.sceneId = null;
    this.live = "";
    this.dropSeen = shared(DROP_KEY)?.id ?? null; // a request from before startup is already handled
    this.dir = `${home()}/.cache/herdr-always-need-cats/sessions`;
    cx.spawn(async (cx) => {
      await this.readSessions();
      cx.notify();
      for (;;) {
        try { await watchFolder(this.dir); } catch { return; }
        await this.readSessions();
        cx.notify();
      }
    });
    cx.timer.every(15000, (cx) => cx.spawn(async (cx) => { await this.readSessions(); cx.notify(); }));
    cx.timer.every(250, (cx) => this.tick(cx));
    // The loop touches its cx on each command: after a mod reload, the old version
    // stops there instead of going on taking the new one's commands.
    cx.spawn(async (cx) => {
      for (;;) {
        const c = await nextCommand();
        cx.notify();
        const list = agents();
        const a = list.find((x) => x.focused) ?? list[0];
        if (!a) continue;
        const coat = assign(list).coats[a.address];
        const tag = tagOf(a, tabsById(), labelsByAddress());
        if (c === "pick") this.openPicker(a, coat, tag);
        // Meal demo (herdr-app do strip-cats.demo-eat): two imaginary files, nothing is sent.
        if (c === "demo-eat") this.feed(a.address, 2);
        // Demo (herdr-app do strip-cats.demo / strip-cats.demo-blocked): the active agent acts
        // as if it had finished (or was waiting for you) for 30 seconds, cat window included.
        if (c === "demo" || c === "demo-blocked") {
          const kind = c === "demo" ? "done" : "blocked";
          this.demo = { address: a.address, mood: kind, until: Date.now() + DEMO_MS };
          this.release(a, kind, coat, tag, true);
        }
      }
    });
  }

  async readSessions() {
    const out = {};
    try {
      for (const f of await fs.readdir(this.dir)) {
        if (!f.endsWith(".json")) continue;
        try {
          const s = JSON.parse(await fs.readFile(`${this.dir}/${f}`, "utf8"));
          if (!s?.terminal) continue;
          const old = out[s.terminal];
          if (!old || (s.seen ?? 0) > (old.seen ?? 0)) out[s.terminal] = s;
        } catch { /* file being written */ }
      }
    } catch { /* no folder yet */ }
    this.sessions = out;
  }

  // Files for this agent: the cat eats them, the mentions go into its prompt.
  drop(address, pane, paths, cx) {
    if (!paths?.length) return;
    this.feed(address, paths.length, cx);
    cx.spawn(async () => {
      try {
        await pasteInto(this.T(), address, pane, await mentionsFor(this.T(), address, paths));
      } catch (e) {
        notify({ title: this.T().notSent, body: String(e?.message ?? e), level: "error" });
      }
    });
  }

  // The meal: it stops, the files fall into its mouth, it chews, then it is happy.
  feed(address, n, cx) {
    const m = this.cats[address];
    if (m) {
      if (m.moving) { m.x = m.target = m.from + (m.target - m.from) * clamp((Date.now() - m.start) / m.dur, 0, 1); m.moving = false; m.dur = 150; }
      m.caught = { at: Date.now(), until: Date.now() + MEAL.full, n, seed: true, stage: "eat" };
      // Drawn at the top first, then at its mouth (next tick): the transition makes the files fall.
    }
    if (cx) cx.notify();
  }

  T() {
    return TEXTS[this.lang] ?? TEXTS.fr;
  }

  sinceOf(address, mood, now) {
    const cur = this.since[address];
    if (!cur || cur.mood !== mood) this.since[address] = { mood, at: now };
    return this.since[address].at;
  }

  // The little cat sets off when it starts waiting for you or finishes (even if you are watching: the end
  // also comes from Claude Code's hook), then every 5 minutes while it waits for you.
  alerts(list, coats, tabs, labels, now, moods) {
    const live = new Set();
    for (const a of list) {
      live.add(a.address);
      const mood = moods[a.address]?.mood;
      const kind = mood === "blocked" ? "blocked" : mood === "done" || mood === "finished" ? "done" : null;
      const last = this.alerted[a.address];
      if (!kind) { delete this.alerted[a.address]; continue; }
      const fresh = !last || last.kind !== kind;
      const again = !fresh && kind === "blocked" && now - last.at >= REALERT;
      if (!fresh && !again) continue;
      this.alerted[a.address] = { kind, at: now };
      if (now - this.startedAt < SETTLE || !alertOn(kind)) continue;
      this.release(a, kind, coats[a.address], tagOf(a, tabs, labels), false);
    }
    for (const k of Object.keys(this.alerted)) if (!live.has(k)) delete this.alerted[k];
  }

  // The strip's cat releases a little cat: a narrow, transparent column, the full height
  // of the window, above it, for as long as the little cat takes to climb it.
  release(a, kind, coat, tag, demo) {
    const m = this.cats[a.address];
    const side = sidebarWidth();
    // Where it is now (when walking: between its start and its destination).
    const f = m?.moving ? clamp((Date.now() - m.start) / m.dur, 0, 1) : 1;
    const here = m ? (m.moving ? m.from + (m.target - m.from) * f : m.x) : this.width / 2;
    const x = Math.round((side + 1 + here) * zoom());
    openOverlay({
      mod: MOD, kind: "window", frame: "none", at: { x: Math.max(0, x - KIT.lane / 2), y: 0 }, width: KIT.lane, height: 1,
      props: { alert: true, phase: "run", demo, x, address: a.address, pane: a.pane, kind, coat, tag },
    });
  }

  tick(cx) {
    const now = Date.now();
    const list = agents();
    const tabs = tabsById();
    const labels = labelsByAddress();
    const { coats } = assign(list);
    // Files dropped on a pane header (cats-pane).
    const req = shared(DROP_KEY);
    if (req?.id && req.id !== this.dropSeen) {
      this.dropSeen = req.id;
      this.drop(req.address, req.pane, req.paths, cx);
    }

    const lo = SLOT / 2;
    const hi = Math.max(lo, this.width - SLOT / 2);
    let changed = false;
    const live = new Set();
    const shown = {};
    list.forEach((a, i) => {
      live.add(a.address);
      const s = this.sessions[a.address];
      let m = this.cats[a.address];
      if (!m) {
        const spot = clamp(((i + 0.5) / list.length) * this.width + rand(-20, 20), lo, hi);
        m = this.cats[a.address] = { x: spot, from: spot, target: spot, dir: "r", moving: false, start: 0, dur: 0, pauseUntil: now + rand(500, 3000), mood: null, crepe: false };
        if (now - this.startedAt > SETTLE) {
          const edge = spot < this.width / 2 ? -SLOT / 2 : this.width + SLOT / 2;
          Object.assign(m, { x: edge, from: edge, dir: edge < spot ? "r" : "l", arriving: true, go: { target: spot, at: now } });
        }
        changed = true;
      }
      const demo = this.demo && this.demo.address === a.address && now < this.demo.until ? this.demo.mood : null;
      const mood = demo ?? moodOf(a, tabs, now, s);
      const since = this.sinceOf(a.address, mood, now);
      const caught = m.caught && now < m.caught.until ? m.caught : null;
      if (m.caught && !caught) { delete m.caught; changed = true; }
      if (caught?.seed) { if (caught.drawn) caught.seed = false; changed = true; } // drawn at the top: it can fall
      if (caught) {
        const stage = now - caught.at < MEAL.chew ? "eat" : "full";
        if (stage !== caught.stage) { caught.stage = stage; changed = true; }
      }
      const T = this.T();
      const files = caught ? T.files(caught.n) : "";
      const says = caught ? (caught.stage === "eat" ? T.eating(files) : T.ate(files, caught.n)) : saysOf(T, mood, s, since, now);
      shown[a.address] = { mood, text: says, since };
      if (mood !== m.mood || says !== m.says) { m.mood = mood; m.says = says; changed = true; }
      const roams = !m.caught && (mood === "working" || mood === "idle");
      if (m.go && now > m.go.at) {
        this.walk(m, m.go.target, (Math.abs(m.go.target - m.x) / (SPEED.working * 1.6)) * 1000, now);
        delete m.go;
        changed = true;
      } else if (m.moving) {
        const f = clamp((now - m.start) / m.dur, 0, 1);
        if (!m.arriving && (m.target < lo || m.target > hi)) {
          m.x = m.target = clamp(m.from + (m.target - m.from) * f, lo, hi);
          m.moving = false;
          m.dur = 150;
          m.pauseUntil = now + rand(1000, 3000);
          changed = true;
        } else if (f >= 1) {
          m.moving = false;
          m.arriving = false;
          m.x = m.target;
          m.crepe = !m.crepe; // while thinking: every other stop, the pancake
          m.pauseUntil = now + (mood === "working" ? rand(3000, 7000) : rand(5000, 14000));
          changed = true;
        } else if (!m.arriving && !roams) {
          m.x = m.target = m.from + (m.target - m.from) * f;
          m.moving = false;
          m.dur = 150;
          changed = true;
        }
      } else if (roams && now >= m.pauseUntil && hi > lo) {
        let target = rand(lo, hi);
        if (Math.abs(target - m.x) < 70) target = m.x + (target >= m.x ? 70 : -70);
        target = clamp(target, lo, hi);
        if (Math.abs(target - m.x) >= 8) {
          this.walk(m, target, (Math.abs(target - m.x) / SPEED[mood]) * 1000, now);
          changed = true;
        } else {
          m.pauseUntil = now + rand(1000, 3000);
        }
      }
      if (!m.moving && !m.arriving && (m.x < lo || m.x > hi)) { m.x = m.target = clamp(m.x, lo, hi); m.dur = 150; changed = true; }
    });
    for (const k of Object.keys(this.cats)) if (!live.has(k)) { delete this.cats[k]; delete this.since[k]; changed = true; }
    this.alerts(list, coats, tabs, labels, now, shown);
    // What each cat says, for the pane headers (only when it changes).
    const json = JSON.stringify(shown);
    if (json !== this.live) { this.live = json; setShared(LIVE_KEY, shown); }
    const sceneId = sceneNow(now)?.id ?? null;
    if (sceneId !== this.sceneId) { this.sceneId = sceneId; changed = true; }
    if (changed) cx.notify();
  }

  walk(m, target, ms, now) {
    m.from = m.x;
    m.target = target;
    m.dir = target > m.x ? "r" : "l";
    m.start = now;
    m.dur = Math.max(1, ms);
    m.moving = true;
  }

  openPicker(a, coat, tag) {
    openOverlay({ mod: MOD, kind: "dialog", width: 580, height: 520, props: { picker: true, address: a.address, current: coat, tag } });
  }

  render(cx) {
    if (this.role === "alert") return this.renderAlert(cx);
    if (this.role === "picker") return this.renderPicker(cx);
    return this.renderStrip(cx);
  }

  sprite(coat, mood, m, activity) {
    if (m.moving) return `${IMG}/cat-${coat}-run-${m.dir}.gif`;
    if (mood === "working") {
      const kind = ACTIVITIES.includes(activity) ? activity : "think";
      return kind === "think" && m.crepe ? `${IMG}/cat-${coat}-think.gif` : `${IMG}/cat-${coat}-work-${kind}.gif`;
    }
    if (mood === "blocked") return `${IMG}/cat-${coat}-question.gif`;
    if (mood === "done") return `${IMG}/cat-${coat}-done.gif`;
    if (mood === "finished") return `${IMG}/cat-${coat}-meow.gif`;
    if (mood === "sleep") return `${IMG}/cat-${coat}-sleep.gif`;
    return `${IMG}/cat-${coat}-idle.gif`;
  }

  renderStrip(_cx) {
    const t = theme();
    const now = Date.now();
    const list = agents();
    const tabs = tabsById();
    const labels = labelsByAddress();
    const { coats } = assign(list);
    const ground = this.height - FEET;
    const scene = sceneNow(now);
    this.sceneId = scene?.id ?? null;

    const root = div()
      .id("strip-cats")
      .relative()
      .size_full()
      .overflow_hidden()
      .bg(t.chrome)
      .on_size_change((size, cx) => {
        const width = size.width / zoom();
        const height = size.height / zoom();
        if (Math.abs(width - this.width) > 1 || Math.abs(height - this.height) > 1) {
          this.width = width;
          this.height = height;
          cx.notify();
        }
      });

    if (scene) {
      const top = this.height - SCENE_H;
      root
        .child(image(`mods/strip-cats/scenes/${scene.id}.png`).absolute().left(0).top(top).w(SCENE_W).h(SCENE_H))
        .child(div().absolute().inset_0().bg(t.chrome).opacity(SCENE_DIM))
        .when(top > 0, (el) => el.children([0.8, 0.55, 0.3, 0.12].map((o, i) =>
          div().absolute().left(0).right(0).top(top + i * 6).h(6).bg(t.chrome).opacity(o))))
        .child(div().absolute().bottom(3).right(8).px(6).rounded(6).bg(alpha(t.chrome, "b3"))
          .text_size(9.5).text_color(t.muted).child(this.T().scenes[scene.id]));
    } else {
      root.child(div().absolute().left(0).right(0).top(ground + 4).h(1).bg(t.border));
    }

    if (list.length === 0) {
      return root.child(div().absolute().inset_0().flex().items_center().justify_center()
        .child(div().px(10).py(4).rounded(8).bg(alpha(t.chrome, "d9")).text_size(12).text_color(t.muted)
          .child(this.T().empty)));
    }

    const xOf = (m) => {
      if (!m) return this.width / 2;
      if (!m.moving) return m.x;
      const f = clamp((now - m.start) / m.dur, 0, 1);
      return m.from + (m.target - m.from) * f;
    };
    // Bubbles and labels never overlap: hovered > waiting > finished > active > the rest.
    const URGENT = { blocked: 1, done: 2, finished: 3 };
    const rank = (a) => (this.hover === a.address ? 0 : URGENT[this.cats[a.address]?.mood] ?? (a.focused ? 4 : 5));
    const fit = (width, placed, x) => {
      const half = width / 2;
      if (!placed.every(([l, r]) => x + half + 6 < l || x - half - 6 > r)) return false;
      placed.push([x - half, x + half]);
      return true;
    };
    const tags = [], bubbles = [];
    const showTag = new Set(), showBubble = new Set();
    for (const a of [...list].sort((x, y) => rank(x) - rank(y))) {
      const m = this.cats[a.address];
      const x = xOf(m);
      if (fit(Math.min(SLOT - 8, tagOf(a, tabs, labels).length * 6 + 18), tags, x)) showTag.add(a.address);
      if (fit(this.bubbleW(m?.says ?? ""), bubbles, x)) showBubble.add(a.address);
    }

    const order = [...list].sort((a, b) => xOf(this.cats[a.address]) - xOf(this.cats[b.address]));
    for (const a of order) {
      const coat = coats[a.address];
      const m = this.cats[a.address] ?? { x: this.width / 2, target: this.width / 2, dir: "r", moving: false, dur: 0 };
      const s = this.sessions[a.address];
      const mood = m.mood ?? moodOf(a, tabs, now, s);
      const tag = tagOf(a, tabs, labels);
      const hovered = this.hover === a.address;
      const x = m.moving ? m.target : m.x;
      const catTop = ground - CAT_H + 3;
      const waited = now - (this.since[a.address]?.at ?? now);

      // Waiting for you: it hops, faster and faster. Finished: it jumps (the GIF), then asks for more.
      const hop = !m.moving && (mood === "blocked" || mood === "finished");
      // A stable id per cat and per animation: the GIF keeps playing from one render to the next.
      // While eating: it chews (mouth opening and closing), then it is happy.
      const file = m.caught ? `${IMG}/cat-${coat}-${m.caught.stage === "eat" ? "meow" : "done"}.gif` : this.sprite(coat, mood, m, s?.activity);
      const cat = image(file).id(`sprite-${a.address}-${file.slice(IMG.length + 1, -4)}`)
        .absolute().left(SLOT / 2 - CAT_W / 2).top(catTop).w(CAT_W).h(CAT_H)
        .when(hop, (el) => el.loop("top", { from: catTop, to: catTop - (mood === "blocked" ? 9 : 5), period: mood === "blocked" && waited > 120000 ? 380 : 650 }));
      const body = div()
        .child(div().absolute().left(SLOT / 2 - 22).top(ground - 2).w(44).h(6).rounded_full().bg("#00000030"))
        .child(cat);

      // The files falling into its mouth: small sheets that shrink as they go in.
      if (m.caught && now - m.caught.at < MEAL.fall + MEAL.stagger * MEAL.papers + 200) {
        const seed = m.caught.seed;
        if (seed) m.caught.drawn = true;
        for (let i = 0; i < Math.min(m.caught.n, MEAL.papers); i++) {
          // Start from a drawn spot: Herdr only animates from a position seen on screen.
          const dur = MEAL.fall + i * MEAL.stagger;
          const w = seed ? 16 : 3, h = seed ? 20 : 4;
          const tx = SLOT / 2 - 2 + (seed ? (i - 1) * 18 : 0);
          body.child(v_flex().id(`paper-${a.address}-${m.caught.at}-${i}`)
            .absolute().left(tx - w / 2).top(seed ? Math.max(0, catTop - 6 - (i % 2) * 8) : catTop + MEAL.mouth - h / 2).w(w).h(h)
            .gap(2).px(seed ? 3 : 0).pt(seed ? 4 : 0).rounded(2).bg(PAPER).border_1().border_color(INK).overflow_hidden()
            .transition("top", { duration: dur, easing: "ease-in" })
            .transition("left", { duration: dur, easing: "ease-in" })
            .transition("width", { duration: dur, easing: "ease-in" })
            .transition("height", { duration: dur, easing: "ease-in" })
            .children(seed ? [0, 1, 2].map((k) => div().h(1).w(k === 2 ? 6 : 9).bg("#2B223066")) : []));
        }
      }
      const kittens = !m.moving && mood !== "sleep" ? Object.values(s?.kittens ?? {}).slice(0, MAX_KITTENS) : [];
      const behind = m.dir === "r" ? -1 : 1;
      kittens.forEach((k, i) => {
        const kind = ACTIVITIES.includes(k.activity) ? k.activity : "think";
        const kx = SLOT / 2 + behind * (CAT_W / 2 + 6 + i * (KIT_W - 10)) - (behind < 0 ? KIT_W : 0);
        body.child(image(`${IMG}/kit-${kittenCoat(k.type)}-${kind}.gif`).id(`kit-${a.address}-${i}-${kind}`).absolute().left(kx).top(ground - KIT_H + 2).w(KIT_W).h(KIT_H));
      });

      const name = hovered ? `${this.T().coats[coat]} · ${tag}` : tag;
      const urgent = mood === "blocked";
      const bubbleW = this.bubbleW(m.says ?? "");
      // Centered on the cat, but never cut off by the strip's edges.
      const bubbleLeft = clamp(SLOT / 2 - bubbleW / 2, 4 - (x - SLOT / 2), this.width - 4 - bubbleW - (x - SLOT / 2));
      root.child(
        div()
          .id(`cat-${a.address}`)
          .absolute().top(0).h_full().w(SLOT)
          .left(x - SLOT / 2)
          .transition("left", { duration: Math.max(1, Math.round(m.moving ? m.dur : m.dur || 150)), easing: "linear" })
          .cursor_pointer()
          .on_hover((h, cx) => {
            const next = h ? a.address : this.hover === a.address ? null : this.hover;
            if (next !== this.hover) { this.hover = next; cx.notify(); }
          })
          .on_click(() => (a.pane ? run("pane.focus", { pane: a.pane }) : run("agent.focus", { terminal: a.address })))
          .on_mouse_down("right", (_e, cx) => {
            cx.stop_propagation();
            this.openPicker(a, coat, tag);
          })
          .on_drop((e, cx) => this.drop(a.address, a.pane, e.paths, cx))
          .child(body)
          .when(showBubble.has(a.address) || hovered, (el) => el.child(
            h_flex().absolute().left(bubbleLeft).w(bubbleW).top(4).h(BUBBLE_H).justify_center()
              .child(this.bubble(m.says ?? "", mood, bubbleW))))
          .when(showTag.has(a.address), (el) => el.child(
            h_flex().absolute().left(4).w(SLOT - 8).top(ground + 6).h(LABEL_H).justify_center().items_center()
              .child(h_flex().min_w(0).h(LABEL_H).px(6).gap(4).items_center().rounded(LABEL_H / 2)
                .bg(urgent ? alpha(t.blocked, "40") : alpha(t.chrome, "d9"))
                .child(div().flex_none().size(6).rounded_full().bg(t[a.status] ?? t.idle)
                  .when(urgent, (d) => d.loop("opacity", { from: 0.35, to: 1, period: 900 })))
                .child(div().min_w(0).truncate().text_size(10.5)
                  .text_color(hovered || a.focused || urgent ? t.foreground : t.muted)
                  .child(name))))),
      );
    }
    return root;
  }

  bubbleW(text) {
    return clamp(text.length * 6 + 18, 54, 210);
  }

  // The bubble above the cat: light with an orange border (waiting) or green (finished), otherwise subtle.
  bubble(text, mood, w) {
    const t = theme();
    const loud = EDGE[mood];
    return div().max_w(w).h(BUBBLE_H).px(7).flex().items_center().rounded(8).text_size(10.5).truncate()
      .when(!!loud, (el) => el.bg(PAPER).border_2().border_color(loud).text_color(INK).font_semibold())
      .when(!loud, (el) => el.bg(alpha(t.popover, "e6")).border_1().border_color(t.border).text_color(mood === "sleep" ? t.muted : t.foreground))
      .child(text);
  }

  // ---- the little cat (props { alert, phase, demo, x, address, pane, kind, coat, tag }) ----

  initAlert(cx) {
    const p = props() ?? {};
    this.closed = false;
    this.openedAt = Date.now();
    this.h = null; // column height (phase "run"), known after the first render
    this.up = false; // the run has started
    this.landed = false;
    if (p.phase === "run") {
      cx.timer.after(600, (cx) => { if (!this.h) { this.h = 800; this.start(cx); } }); // just in case
    } else {
      cx.timer.after(60, (cx) => { this.landed = true; cx.notify(); });
    }
    cx.timer.every(400, () => { if (this.over(p)) this.close(); });
  }

  // It starts from the strip's floor and climbs to the middle; once there, it perches in a small window.
  start(cx) {
    cx.timer.after(40, (cx) => { this.up = true; cx.notify(); });
    cx.timer.after(40 + KIT.run, () => {
      const p = props() ?? {};
      if (this.closed || this.over(p)) return this.close();
      openOverlay({
        mod: MOD, kind: "window", frame: "none", key: `strip-cats-alert-${p.address}`,
        at: { x: Math.max(0, p.x - KIT.w / 2 - 4), y: Math.round((perchY(this.h ?? 800) - 6) * zoom()) },
        props: { ...p, phase: "perch" },
      });
      this.close();
    });
  }

  // Nothing left to say: it no longer waits for you, or it went back to work. (Looking at its pane does
  // not send it away: a click on it or × does.)
  over(p) {
    if (p.demo) return Date.now() - this.openedAt > DEMO_MS;
    const a = agents().find((x) => x.address === p.address);
    return !a || (p.kind === "blocked" ? a.status !== "blocked" : a.status === "working" || a.status === "blocked");
  }

  close() {
    if (this.closed) return;
    this.closed = true;
    closeOverlay(props().overlay);
  }

  go(p) {
    if (p.pane) run("pane.focus", { pane: p.pane });
    else run("agent.focus", { terminal: p.address });
    this.close();
  }

  renderAlert(_cx) {
    const p = props() ?? {};
    const coat = COATS.includes(p.coat) ? p.coat : "ginger";
    const blocked = p.kind === "blocked";
    if (p.phase === "run") {
      // The run: from the strip's floor to the middle of the window, trotting.
      const from = (this.h ?? 800) - KIT.statusbar - FEET - KIT.h;
      return div().id("kit-lane").size_full().relative()
        .on_size_change((size, cx) => {
          if (this.h) return;
          this.h = size.height / zoom();
          this.start(cx);
          cx.notify();
        })
        .when(!!this.h, (el) => el.child(image(`${IMG}/cat-${coat}-run-r.gif`).id("kit-run")
          .absolute().left(KIT.lane / 2 - KIT.w / 2).top(this.up ? perchY(this.h ?? 800) : from).w(KIT.w).h(KIT.h)
          .transition("top", { duration: KIT.run, easing: "ease-in-out" })));
    }
    if (this.closed || this.over(p)) return div();
    const text = shared(LIVE_KEY)?.[p.address]?.text ?? (blocked ? this.T().needsYou : this.T().doneAsk);
    // Perched in the middle: it hops next to its little bubble. A click on it or the bubble: its pane.
    return h_flex()
      .id("kit-perch")
      .items_end().gap(2).cursor_pointer()
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click(() => this.go(p))
      .child(div().id("kit-box").relative().flex_none().w(KIT.w + 4).h(KIT.h + 10)
        .child(div().id("kit-land").absolute().left(2).top(this.landed ? 6 : 30).w(KIT.w).h(KIT.h)
          .spring("top", { response: 380, damping: 0.4 })
          .child(image(`${IMG}/cat-${coat}-${blocked ? "question" : "done"}.gif`).id("kit-hop")
            .absolute().left(0).w(KIT.w).h(KIT.h)
            .loop("top", { from: 0, to: blocked ? -6 : -3, period: blocked ? 560 : 900 }))))
      .child(h_flex().mb(12).max_w(260).h(BUBBLE_H).pl(7).pr(3).gap(4).items_center().rounded(8)
        .bg(PAPER).border_2().border_color(EDGE[p.kind] ?? INK).text_size(10.5).text_color(INK)
        .child(div().flex_none().text_color("#2B223099").child(p.tag ?? "agent"))
        .child(div().min_w(0).truncate().font_semibold().child(text))
        .child(div().id("kit-x").flex_none().px(3).rounded(4).text_color("#2B223099")
          .hover((el) => el.bg("#2B223014"))
          .on_click((_e, cx) => { cx.stop_propagation(); this.close(); })
          .child("×")));
  }

  // ---- the menu (dialog with props { picker, slot, current, tag }) -------------------

  row(t, label, opts) {
    return h_flex().items_start().gap(10).flex_none()
      .child(div().w(132).pt(5).flex_none().text_size(11.5).text_color(t.muted).child(label))
      .child(h_flex().flex_1().min_w(0).flex_wrap().gap(4)
        .children(opts.map((o) => div()
          .id(o.id)
          .px(9).h(24).flex().items_center().rounded(6).text_size(11.5).cursor_pointer()
          .border_1().border_color(o.on ? t.border : "#00000000")
          .bg(o.on ? t.selected : "#00000000")
          .text_color(o.on ? t.foreground : t.muted)
          .hover((el) => el.bg(t.hover))
          .on_click((_e, cx) => { o.set(); cx.notify(); })
          .child(o.label))));
  }

  yesNo(t, id, key) {
    const T = this.T();
    return [
      { id: `${id}-yes`, label: T.yes, on: on(key), set: () => setShared(key, true) },
      { id: `${id}-no`, label: T.no, on: !on(key), set: () => setShared(key, false) },
    ];
  }

  choose(coat) {
    const p = props();
    savePicks({ [p.address]: coat });
    closeOverlay(p.overlay);
  }

  renderPicker(_cx) {
    const t = theme();
    const T = this.T();
    const p = props() ?? {};
    const scene = sceneChoice();
    const alert = { blocked: alertOn("blocked"), done: alertOn("done") };
    const setAlert = (k) => setShared(ALERT_KEY, { ...alert, [k]: !alert[k] });
    return v_flex()
      .id("cats-picker")
      .size_full().min_h(0).p(18).gap(12)
      .bg(t.popover)
      .child(h_flex().items_center().justify_between()
        .child(v_flex().min_w(0).gap(2)
          .child(div().text_size(15).font_semibold().text_color(t.foreground).child(T.pickTitle))
          .child(div().text_size(11.5).text_color(t.muted).truncate()
            .child(T.pickFor(p.tag, T.coats[p.current]))))
        .child(div().text_size(11).text_color(t.dim).child(T.esc)))
      .child(this.row(t, T.scene, [{ id: "shuffle", label: T.shuffle }, ...SCENES.map((x) => ({ id: x.id, label: T.scenes[x.id] })), { id: "off", label: T.none }]
        .map((o) => ({ id: `scene-${o.id}`, label: o.label, on: o.id === scene, set: () => setShared(SCENE_KEY, o.id) }))))
      .child(this.row(t, T.alertRow, [
        { id: "alert-blocked", label: T.alertBlocked, check: true, on: alert.blocked, set: () => setAlert("blocked") },
        { id: "alert-done", label: T.alertDone, check: true, on: alert.done, set: () => setAlert("done") },
      ]))
      .child(this.row(t, T.headerRow, this.yesNo(t, "header", HEADER_KEY)))
      .child(div().text_size(11.5).text_color(t.muted).child(T.coat))
      .child(h_flex().flex_wrap().gap(8).children(COATS.map((coat) => {
        const current = coat === p.current;
        return v_flex()
          .id(`pick-${coat}`)
          .w(120).h(112).flex_none().items_center().justify_center().gap(4)
          .rounded(10).border_1()
          .border_color(current ? t.accent : t.border)
          .bg(current ? t.selected : "#00000000")
          .hover((s) => s.bg(t.hover))
          .cursor_pointer()
          .on_click(() => this.choose(coat))
          .child(image(`${IMG}/cat-${coat}-idle.gif`).w(CAT_W).h(CAT_H).flex_none())
          .child(div().text_size(12).text_color(t.foreground).child(T.coats[coat]));
      })));
  }
}

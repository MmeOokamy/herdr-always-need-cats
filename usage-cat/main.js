// usage-cat : le chat d'usage, dans la barre latérale de Herdr.
//
// Il lit les chiffres que statusline.py (status line de Claude Code)
// écrit dans ~/.cache/usage-cat/state.json : session de 5 heures et semaine.
// Les images animées sont générées par tools/make_sprites.py.
//
// Bloc de la barre latérale de Herdr, entre Spaces et Agents.
// props (dans le layout) : { config: chemin du config.json, root: dossier du clone }
//
// Mises à jour : une fois par jour, le mod lance `updates.py --check` ; quand
// une nouvelle version est publiée, il le signale (ligne cliquable et
// notification), et un clic lance `updates.py`, qui met le clone à jour.

import { View, div, image } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { exec, home, nextCommand, notify, props, readTextFile, theme } from "herdr";

const WINDOWS = ["five_hour", "seven_day"];
const LEVELS = ["none", "ok", "warn", "alert", "critical", "full"];
const LEVEL_COLOR = {
  none: "#868E96",
  ok: "#2F9E44",
  warn: "#F2B01E",
  alert: "#E8590C",
  critical: "#E03131",
  full: "#E03131",
};
const OUTLINE = "#2B2230";
const CREAM = "#FFFDF5";
const HALO = "#FFFFFFD9";
const COATS = ["ginger", "grey", "black", "cream", "brown", "blue"];

const ACTIVE_SECONDS = 20; // le chat tape après l'arrivée de chiffres frais
const CELEBRATION_SECONDS = 30; // saute de joie après un reset
const POLL_MS = 2000;

const UPDATE_POLL_MS = 60 * 1000; // relecture de l'état des mises à jour
const UPDATE_EVERY = 24 * 3600; // vérification automatique, en secondes
const UPDATE_RETRY = 3600; // après une vérification en échec (hors ligne...)

const CAT_W = 66; // taille affichée de l'image (générée en 176 x 200)
const CAT_H = 75;

const TEXTS = {
  fr: {
    title: "Usage Claude Code",
    renewed_title: "Session rechargée !",
    five_hour: "Session",
    seven_day: "Semaine",
    line: (l, p, w, d) => `${l} : ${p} % · reset ${w} (${d})`,
    full: (l, w, d) => `${l} : épuisée · reprise ${w} (${d})`,
    renewed: (l) => `${l} : 0 % (réinitialisée)`,
    delay: (d) => `dans ${d}`,
    waiting: "en attente de Claude Code…",
    days: ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."],
    day_unit: "j",
    pct: (p) => `${p} %`,
    reset: (w, d) => `reset ${w} (${d})`,
    back: (w, d) => `reprise ${w} (${d})`,
    renewed_short: "réinitialisée",
    update_title: "herdr-always-need-cats",
    update_available: (v) => `Mise à jour ${v} disponible`,
    update_changes: (n) => `${n} changement${n > 1 ? "s" : ""} : cliquer pour mettre à jour`,
    update_short: "MAJ",
    update_blocked: (why) => `Mise à jour ${why}`,
    blocked: { dirty: "bloquée : modifications locales", ahead: "bloquée : commits locaux" },
    updating: "Mise à jour…",
    update_done: (v) => `Version ${v} installée.`,
    update_failed: (e) => `Mise à jour impossible : ${e}`,
  },
  en: {
    title: "Claude Code usage",
    renewed_title: "Session refilled!",
    five_hour: "Session",
    seven_day: "Week",
    line: (l, p, w, d) => `${l}: ${p}% · resets ${w} (${d})`,
    full: (l, w, d) => `${l}: limit reached · back ${w} (${d})`,
    renewed: (l) => `${l}: 0% (reset)`,
    delay: (d) => `in ${d}`,
    waiting: "waiting for Claude Code…",
    days: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    day_unit: "d",
    pct: (p) => `${p}%`,
    reset: (w, d) => `resets ${w} (${d})`,
    back: (w, d) => `back ${w} (${d})`,
    renewed_short: "reset",
    update_title: "herdr-always-need-cats",
    update_available: (v) => `Update ${v} available`,
    update_changes: (n) => `${n} change${n > 1 ? "s" : ""}: click to update`,
    update_short: "UPD",
    update_blocked: (why) => `Update ${why}`,
    blocked: { dirty: "blocked: local changes", ahead: "blocked: local commits" },
    updating: "Updating…",
    update_done: (v) => `Version ${v} installed.`,
    update_failed: (e) => `Update failed: ${e}`,
  },
};

export default class UsageCat extends View {
  init(_props, cx) {
    this.settings = { lang: "fr", coat: "ginger", warn: 50, alert: 80, critical: 95, notify_seconds: 12 };
    this.text = TEXTS.fr;
    this.raw = null; // dernier contenu lu de state.json
    this.state = {};
    this.level = "none";
    this.activeUntil = 0;
    this.celebrateUntil = 0;
    this.signature = null;
    cx.spawn(async (cx) => {
      await this.loadSettings();
      await this.poll(cx, true);
      cx.notify();
    });
    cx.timer.every(POLL_MS, (cx) => {
      cx.spawn(async (cx) => this.poll(cx, false));
    });

    this.updates = {}; // état écrit par updates.py
    this.updating = null; // "check" ou "update" pendant que updates.py tourne
    this.lastCheck = 0; // dernière vérification lancée d'ici
    this.notified = null; // version déjà signalée par une notification
    cx.spawn(async (cx) => this.pollUpdates(cx));
    cx.timer.every(UPDATE_POLL_MS, (cx) => {
      cx.spawn(async (cx) => this.pollUpdates(cx));
    });
    // Clic sur la notification : run("usage-cat.update")
    cx.spawn(async (cx) => {
      for (;;) {
        const command = await nextCommand();
        if (command === "update") await this.runUpdates(cx, "update");
      }
    });
  }

  // --- Mises à jour --------------------------------------------------------

  root() {
    const p = props() ?? {};
    return p.root ?? (p.config ? p.config.replace(/\/[^/]*$/, "") : null);
  }

  async readUpdates() {
    try {
      const data = JSON.parse((await readTextFile(`${home()}/.cache/herdr-always-need-cats/updates.json`)) ?? "{}");
      this.updates = data && typeof data === "object" ? data : {};
    } catch (_e) {
      this.updates = {};
    }
  }

  updateAvailable() {
    const u = this.updates;
    return Boolean(u.behind) && !u.dirty && !u.ahead && !u.error;
  }

  updateBlocked() {
    const u = this.updates;
    if (!u.behind || u.error) return null;
    return u.dirty ? "dirty" : u.ahead ? "ahead" : null;
  }

  latest() {
    return String(this.updates.latest ?? "").replace(/^v/, "");
  }

  async pollUpdates(cx) {
    if (this.updating) return;
    const before = JSON.stringify(this.updates);
    await this.readUpdates();
    const now = Date.now() / 1000;
    const due = now - (this.updates.checked ?? 0) > UPDATE_EVERY;
    if (due && now - this.lastCheck > UPDATE_RETRY) {
      this.lastCheck = now;
      await this.runUpdates(cx, "check");
      return;
    }
    this.announce();
    if (JSON.stringify(this.updates) !== before) cx.notify();
  }

  // Une notification par nouvelle version ; un clic dessus met à jour.
  announce() {
    if (!this.updateAvailable() || this.notified === this.updates.latest) return;
    this.notified = this.updates.latest;
    const count = (this.updates.changes ?? []).length || this.updates.behind;
    notify({
      title: this.text.update_available(this.latest()),
      body: this.text.update_changes(count),
      level: "info",
      action: { name: "usage-cat.update" },
    });
  }

  // updates.py --check, ou updates.py (met à jour puis relance install.py).
  async runUpdates(cx, what) {
    const root = this.root();
    if (!root || this.updating) return;
    if (what === "update" && !this.updateAvailable()) return;
    const version = this.latest();
    const target = this.updates.latest;
    this.updating = what;
    cx.notify();
    let result = null;
    try {
      const args = [`${root}/updates.py`, ...(what === "check" ? ["--check"] : [])];
      result = await exec("python3", args, { cwd: root, timeout: 300000 });
    } catch (e) {
      result = { code: 1, stdout: "", stderr: String(e) };
    }
    this.updating = null;
    await this.readUpdates();
    if (what === "update") {
      // Réussie si le clone est maintenant sur la version annoncée.
      const ok = result.code === 0 && this.updates.version === target;
      const lines = `${result.stderr}\n${result.stdout}`.trim().split("\n");
      notify({
        title: this.text.update_title,
        body: ok ? this.text.update_done(version) : this.text.update_failed(this.updates.error ?? lines[lines.length - 1]),
        level: ok ? "success" : "error",
      });
    } else {
      this.announce();
    }
    cx.notify();
  }

  async loadSettings() {
    const path = props()?.config;
    if (!path) return;
    try {
      const data = JSON.parse((await readTextFile(path)) ?? "{}");
      if (data && typeof data === "object") Object.assign(this.settings, data);
    } catch (_e) {
      // config absente ou invalide : réglages par défaut
    }
    this.text = TEXTS[String(this.settings.lang).toLowerCase()] ?? TEXTS.fr;
    if (!COATS.includes(this.settings.coat)) this.settings.coat = "ginger";
  }

  async poll(cx, first) {
    const now = Date.now() / 1000;
    let raw = null;
    try {
      raw = await readTextFile(`${home()}/.cache/usage-cat/state.json`);
    } catch (_e) {
      raw = null;
    }
    if (raw !== null && raw !== this.raw) {
      try {
        const state = JSON.parse(raw);
        if (state && typeof state === "object") {
          this.state = state;
          if (!first || now - (state.ts ?? 0) < ACTIVE_SECONDS) {
            this.activeUntil = now + ACTIVE_SECONDS;
          }
        }
      } catch (_e) {
        // fichier en cours d'écriture : relu au prochain passage
      }
      this.raw = raw;
    }
    this.updateLevel(now, first);
    // Redessiner seulement quand ce qui est affiché change (au plus une fois
    // par minute pour les délais affichés).
    const signature = JSON.stringify([
      this.animation(now),
      this.level,
      WINDOWS.map((n) => this.window(n, now)),
      Math.floor(now / 60),
    ]);
    if (signature !== this.signature) {
      this.signature = signature;
      cx.notify();
    }
  }

  // --- Chiffres ------------------------------------------------------------

  window(name, now) {
    const data = this.state[name];
    if (!data || typeof data !== "object" || data.pct === null || data.pct === undefined) {
      return [null, null];
    }
    const reset = data.resets_at;
    if (reset && now >= reset) return [0, null];
    return [Math.min(100, Math.max(0, Math.trunc(data.pct))), reset ?? null];
  }

  levelOf(pct) {
    if (pct === null) return "none";
    if (pct >= 100) return "full";
    for (const name of ["critical", "alert", "warn"]) {
      if (pct >= this.settings[name]) return name;
    }
    return "ok";
  }

  updateLevel(now, first) {
    const level = WINDOWS.map((n) => this.levelOf(this.window(n, now)[0]))
      .reduce((a, b) => (LEVELS.indexOf(b) > LEVELS.indexOf(a) ? b : a), "none");
    const before = LEVELS.indexOf(this.level);
    const after = LEVELS.indexOf(level);
    if (!first && after > before) {
      if (after >= LEVELS.indexOf("alert")) {
        notify({
          title: this.text.title,
          body: this.lines(now).map((l) => `${l[0]} · ${l[1]}`).join("\n"),
          level: after >= LEVELS.indexOf("critical") ? "error" : "warning",
        });
      }
    } else if (before >= LEVELS.indexOf("alert") && after < LEVELS.indexOf("alert")) {
      this.celebrateUntil = now + CELEBRATION_SECONDS;
    }
    this.level = level;
  }

  animation(now) {
    if (now < this.celebrateUntil) return "done";
    if (this.level === "full") return "sleep";
    if (this.level === "critical") return "panic";
    if (this.level === "alert") return "question";
    if (now < this.activeUntil) return "work";
    return "idle";
  }

  // --- Textes --------------------------------------------------------------

  formatReset(reset, now) {
    const then = new Date(reset * 1000);
    const today = new Date(now * 1000);
    const clock = `${String(then.getHours()).padStart(2, "0")}:${String(then.getMinutes()).padStart(2, "0")}`;
    if (then.toDateString() === today.toDateString()) return clock;
    return `${this.text.days[(then.getDay() + 6) % 7]} ${clock}`;
  }

  formatDelay(seconds) {
    const minutes = Math.max(1, Math.floor(seconds / 60));
    let duration;
    if (minutes < 60) duration = `${minutes} min`;
    else if (minutes < 48 * 60) duration = `${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, "0")}`;
    else duration = `${Math.floor(minutes / (24 * 60))} ${this.text.day_unit}`;
    return this.text.delay(duration);
  }

  lines(now) {
    // Une entrée par fenêtre : [titre, détail, niveau]
    const lines = [];
    for (const name of WINDOWS) {
      const [pct, reset] = this.window(name, now);
      if (pct === null) continue;
      const label = this.text[name];
      const level = this.levelOf(pct);
      if (reset === null) lines.push([`${label} 0 %`, this.text.renewed_short, level]);
      else if (pct >= 100) lines.push([`${label} ${this.text.pct(100)}`, this.text.back(this.formatReset(reset, now), this.formatDelay(reset - now)), level]);
      else lines.push([`${label} ${this.text.pct(pct)}`, this.text.reset(this.formatReset(reset, now), this.formatDelay(reset - now)), level]);
    }
    return lines;
  }

  // --- Dessin --------------------------------------------------------------

  bar(pct, height) {
    const inner = CAT_W - 6;
    const fill = pct ? Math.max(2, Math.round((inner * pct) / 100)) : 0;
    return div().w(CAT_W).h(height + 2).bg(HALO).p(1)
      .child(div().size_full().bg(OUTLINE).p(2)
        .child(div().size_full().bg(CREAM)
          .child(div().h_full().w(fill).bg(LEVEL_COLOR[this.levelOf(pct)]))));
  }

  // Ligne des mises à jour, sous les fenêtres d'usage (null : rien à dire).
  updateLine(t) {
    if (this.updating === "update") {
      return div().truncate().font_semibold().text_color(t.foreground).child(this.text.updating);
    }
    const blocked = this.updateBlocked();
    if (blocked) {
      return div().truncate().text_color(t.dim).child(this.text.update_blocked(this.text.blocked[blocked]));
    }
    if (!this.updateAvailable()) return null;
    const color = t.accent ?? LEVEL_COLOR.ok;
    const count = (this.updates.changes ?? []).length || this.updates.behind;
    // Une seule ligne (le bloc a une hauteur fixe) ; le détail en infobulle.
    return h_flex()
      .id("usage-cat-update")
      .gap(6)
      .items_center()
      .cursor_pointer()
      .tooltip(this.text.update_changes(count))
      .on_click((_e, cx) => cx.spawn(async (cx) => this.runUpdates(cx, "update")))
      .child(div().size(7).flex_none().rounded(4).bg(color))
      .child(div().truncate().font_semibold().text_color(color).child(this.text.update_available(this.latest())));
  }

  render() {
    const t = theme();
    const now = Date.now() / 1000;
    const animation = this.animation(now);
    const [session] = this.window("five_hour", now);
    const [week] = this.window("seven_day", now);
    const sprite = `mods/usage-cat/sprites/${this.settings.coat}-${animation}-${this.level}.webp`;
    const lines = this.lines(now);
    const title = animation === "done" ? this.text.renewed_title : this.text.title;
    const wide = (this.width ?? 268) >= 200;
    const available = this.updateAvailable();
    const cat = v_flex().gap(4).flex_none()
      .child(image(sprite).w(CAT_W).h(CAT_H))
      .child(v_flex().gap(2).child(this.bar(session, 10)).child(this.bar(week, 6)))
      // Barre latérale repliée : le texte est masqué, une étiquette le remplace.
      .when(!wide && (available || this.updating === "update"), (el) => el.child(div()
        .id("usage-cat-update-short")
        .w(CAT_W).rounded(4).bg(t.accent ?? LEVEL_COLOR.ok).text_color(t.accent_foreground ?? CREAM)
        .text_size(10).font_semibold().text_center()
        .when(available, (b) => b.cursor_pointer().on_click((_e, cx) => cx.spawn(async (cx) => this.runUpdates(cx, "update"))))
        .child(this.updating === "update" ? "..." : this.text.update_short)));
    const update = this.updateLine(t);
    const info = v_flex().flex_1().min_w(0).gap(6).text_size(11.8).text_color(t.muted)
      .child(div().font_semibold().truncate().text_color(LEVELS.indexOf(this.level) >= 3 ? LEVEL_COLOR[this.level] : t.foreground).child(title))
      .when(lines.length === 0, (el) => el.child(div().text_color(t.dim).child(this.text.waiting)))
      .children(lines.map(([head, detail, level]) => v_flex()
        .child(h_flex().gap(6).items_center()
          .child(div().size(7).rounded(4).bg(LEVEL_COLOR[level]))
          .child(div().font_semibold().text_color(t.foreground).child(head)))
        .child(div().truncate().text_color(t.dim).child(detail))))
      .when(Boolean(update), (el) => el.child(update));
    return h_flex().id("usage-cat").size_full().px(12).py(6).gap(12).items_center()
      .border_t(1).border_b(1).border_color(t.border)
      .on_size_change((size, cx) => {
        if (Math.abs((this.width ?? 0) - size.width) > 1) {
          this.width = size.width;
          cx.notify();
        }
      })
      .child(cat)
      .when(wide, (el) => el.child(info));
  }
}

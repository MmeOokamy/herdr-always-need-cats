// usage-cat : le chat d'usage, dans la barre latérale de Herdr.
//
// Il lit les chiffres que statusline.py (status line de Claude Code)
// écrit dans ~/.cache/usage-cat/state.json : session de 5 heures et semaine.
// Les images animées sont générées par tools/make_sprites.py.
//
// Bloc de la barre latérale de Herdr, entre Spaces et Agents.
// props (dans le layout) : { config: chemin du config.json de herdr-always-need-cats }

import { View, div, image } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { home, notify, props, readTextFile, theme } from "herdr";

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
    const cat = v_flex().gap(4).flex_none()
      .child(image(sprite).w(CAT_W).h(CAT_H))
      .child(v_flex().gap(2).child(this.bar(session, 10)).child(this.bar(week, 6)));
    const info = v_flex().flex_1().min_w(0).gap(6).text_size(11.8).text_color(t.muted)
      .child(div().font_semibold().truncate().text_color(LEVELS.indexOf(this.level) >= 3 ? LEVEL_COLOR[this.level] : t.foreground).child(title))
      .when(lines.length === 0, (el) => el.child(div().text_color(t.dim).child(this.text.waiting)))
      .children(lines.map(([head, detail, level]) => v_flex()
        .child(h_flex().gap(6).items_center()
          .child(div().size(7).rounded(4).bg(LEVEL_COLOR[level]))
          .child(div().font_semibold().text_color(t.foreground).child(head)))
        .child(div().truncate().text_color(t.dim).child(detail))));
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

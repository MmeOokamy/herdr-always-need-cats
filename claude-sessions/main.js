// claude-sessions : toutes les sessions Claude Code enregistrées
// (~/.claude/projects), de la plus récente à la plus ancienne, dans une
// fenêtre ouverte par mod.open:claude-sessions (raccourci posé par
// install.py). Taper pour filtrer, haut/bas et Entrée pour choisir, Echap
// pour fermer.
//
// Clic droit sur une session : menu (reprendre ou afficher, supprimer).
// Supprimer demande confirmation, puis met la session à la corbeille
// (sessions.py --delete) ; une session ouverte ne peut pas être supprimée.
//
// Entrée sur une session :
// - fermée : la reprend (claude --resume <id>) dans un nouvel onglet, dans
//   l'espace Herdr de son dossier s'il y en a un, sinon dans un nouvel espace ;
// - ouverte dans Herdr : affiche son agent ;
// - ouverte hors de Herdr : rien (la reprendre ferait deux sessions sur le
//   même historique), la ligne le dit.
//
// La lecture des fichiers est faite par sessions.py (à côté, mis en cache).

import { View, div, svg } from "gpui-kit";
import { v_flex, h_flex, InputState, Input, ScrollHandle } from "gpui-base";
import { appHome, checking, closeOverlay, exec, panes, props, readTextFile, run, settings, spaces, theme } from "herdr";

const DIR = "mods/claude-sessions";
// La fenêtre prend la taille de son contenu : la liste a une hauteur fixe.
const ROW = 48;
const LIST_MAX = 528;
const MENU_WIDTH = 230;
const MONTHS = {
  fr: ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
  en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
};
const TEXTS = {
  fr: {
    title: "Sessions Claude",
    filter: "Filtrer par titre, projet, demande…",
    loading: "Lecture des sessions…",
    empty: "Aucune session enregistrée",
    none: "Aucune session ne correspond",
    error: "Lecture impossible",
    prompts: (n) => `${n} demande${n > 1 ? "s" : ""}`,
    count: (n, all) => (n === all ? `${all} session${all > 1 ? "s" : ""}` : `${n} sur ${all}`),
    open: "ouverte",
    elsewhere: "ouverte hors de Herdr",
    resume: "Entrée : reprendre",
    show: "Entrée : afficher",
    now: "à l'instant",
    minutes: (n) => `il y a ${n} min`,
    hours: (n) => `il y a ${n} h`,
    yesterday: "hier",
    days: (n) => `il y a ${n} j`,
    menuResume: "Reprendre",
    menuShow: "Afficher",
    menuDelete: "Supprimer la session",
    menuOpen: "ouverte : la fermer d'abord",
    confirmTitle: "Supprimer la session ?",
    confirmText: "Êtes-vous sûr de supprimer la session",
    confirmNote: "Elle part à la corbeille, avec son historique de fichiers.",
    cancel: "Annuler",
    remove: "Supprimer",
    removing: "Suppression…",
  },
  en: {
    title: "Claude sessions",
    filter: "Filter by title, project, prompt…",
    loading: "Reading sessions…",
    empty: "No saved session",
    none: "No session matches",
    error: "Cannot read sessions",
    prompts: (n) => `${n} prompt${n > 1 ? "s" : ""}`,
    count: (n, all) => (n === all ? `${all} session${all > 1 ? "s" : ""}` : `${n} of ${all}`),
    open: "open",
    elsewhere: "open outside Herdr",
    resume: "Enter: resume",
    show: "Enter: show",
    now: "just now",
    minutes: (n) => `${n} min ago`,
    hours: (n) => `${n} h ago`,
    yesterday: "yesterday",
    days: (n) => `${n} d ago`,
    menuResume: "Resume",
    menuShow: "Show",
    menuDelete: "Delete session",
    menuOpen: "open: close it first",
    confirmTitle: "Delete the session?",
    confirmText: "Are you sure you want to delete the session",
    confirmNote: "It goes to the trash, with its file history.",
    cancel: "Cancel",
    remove: "Delete",
    removing: "Deleting…",
  },
};

function when(seconds, lang) {
  const text = TEXTS[lang];
  const age = Date.now() / 1000 - seconds;
  if (age < 60) return text.now;
  if (age < 3600) return text.minutes(Math.floor(age / 60));
  if (age < 86400) return text.hours(Math.floor(age / 3600));
  if (age < 2 * 86400) return text.yesterday;
  if (age < 7 * 86400) return text.days(Math.floor(age / 86400));
  const d = new Date(seconds * 1000);
  const month = MONTHS[lang][d.getMonth()];
  const year = d.getFullYear() === new Date().getFullYear() ? "" : ` ${d.getFullYear()}`;
  return lang === "en" ? `${month} ${d.getDate()}${year}` : `${d.getDate()} ${month}${year}`;
}

export default class ClaudeSessions extends View {
  init(_props, cx) {
    this.lang = "fr";
    this.sessions = null; // null : en cours de lecture
    this.error = null;
    this.filter = "";
    this.at = 0;
    this.menu = null; // { s, x, y } : menu du clic droit
    this.origin = null; // coin haut gauche de la fenêtre, en coordonnées de la fenêtre Herdr
    this.confirm = null; // { s, busy, error } : confirmation de suppression
    this.handle = cx.focus_handle();
    this.scroll = ScrollHandle.new();
    this.input = null; // créé une fois la langue connue (texte d'aide)
    cx.timer.after(600, () => this.input?.focus());
    cx.spawn(async (cx) => {
      try {
        // Le dossier du mod est un lien vers le clone : config.json est à côté.
        const data = JSON.parse((await readTextFile(`${appHome()}/${DIR}/../config.json`)) ?? "{}");
        const lang = String(data?.lang ?? "fr").toLowerCase();
        if (TEXTS[lang]) this.lang = lang;
      } catch {
        // pas de config : français
      }
      this.makeInput();
      cx.notify();
      if (checking()) {
        this.sessions = [];
        return;
      }
      try {
        const r = await exec("python3", [`${appHome()}/${DIR}/sessions.py`], { timeout: 120000 });
        if (r.code !== 0) throw new Error(r.stderr.trim().split("\n").pop() || `code ${r.code}`);
        this.sessions = JSON.parse(r.stdout).sessions ?? [];
      } catch (e) {
        this.error = String(e?.message ?? e);
        this.sessions = [];
      }
      cx.notify();
    });
  }

  makeInput() {
    this.input = InputState.new({ placeholder: TEXTS[this.lang].filter });
    this.input.on("change", (_e, cx) => {
      this.filter = this.input.value();
      this.at = 0;
      this.scroll.scroll_to_item(0);
      cx.notify();
    });
    this.input.on("submit", (_e, cx) => this.choose(this.rows()[this.at], cx));
    this.input.focus();
  }

  close() {
    closeOverlay(props().overlay);
  }

  // Clic droit : la ligne note la session et le point, la racine (qui reçoit
  // le même clic, avant ou après) donne son origine pour placer le menu.
  placeMenu() {
    const m = this.menu;
    if (!m || m.x != null || !this.origin) return;
    const zoom = settings().zoom || 1;
    const width = this.size?.width ?? 720;
    m.x = Math.max(4, Math.min((m.at.x - this.origin.x) / zoom, width - MENU_WIDTH - 4));
    const y = (m.at.y - this.origin.y) / zoom;
    // La fenêtre coupe ce qui dépasse : sans place en dessous, le menu
    // s'ouvre au-dessus du pointeur.
    const height = this.size?.height ?? Infinity;
    const menu = this.menuHeight(m.s);
    m.y = y + menu + 4 > height ? Math.max(4, y - menu) : y;
  }

  // Hauteur du menu (voir renderMenu) : marges 2 x 4, lignes de 30 séparées
  // de 2, et la mention d'une session ouverte (environ 22).
  menuHeight(s) {
    const items = s.running && !s.terminal ? 1 : 2;
    return 8 + items * 30 + (items - 1) * 2 + (s.running ? 24 : 0);
  }

  askDelete(s) {
    this.menu = null;
    this.confirm = { s, busy: false, error: null };
    this.handle.focus(); // Entrée et Echap vont à la confirmation, pas au filtre
  }

  cancelDelete() {
    this.confirm = null;
    this.input?.focus();
  }

  doDelete(cx) {
    const c = this.confirm;
    if (!c || c.busy) return;
    c.busy = true;
    c.error = null;
    cx.notify();
    cx.spawn(async (cx) => {
      try {
        const r = await exec("python3", [`${appHome()}/${DIR}/sessions.py`, "--delete", c.s.id], { timeout: 60000 });
        const out = JSON.parse(r.stdout || "{}");
        if (out.error || r.code !== 0) throw new Error(out.error || r.stderr.trim() || `code ${r.code}`);
        this.sessions = (this.sessions ?? []).filter((x) => x.id !== c.s.id);
        this.cancelDelete();
      } catch (e) {
        c.busy = false;
        c.error = String(e?.message ?? e);
      }
      cx.notify();
    });
  }

  renderMenu(t, text) {
    const m = this.menu;
    if (!m || m.x == null) return null;
    const s = m.s;
    const item = (id, label, enabled, action, color) => h_flex().id(id).h(30).px(10).gap(8).items_center().rounded(6)
      .text_color(enabled ? (color ?? t.foreground) : t.dim)
      .when(enabled, (el) => el.cursor_pointer().hover((st) => st.bg(t.hover)))
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .on_click((_e, cx) => {
        if (!enabled) return;
        action(cx);
        cx.notify();
      })
      .child(label);
    const open = s.running ? (s.terminal ? text.menuShow : null) : text.menuResume;
    return v_flex().absolute().left(m.x).top(m.y).w(MENU_WIDTH).p(4).gap(2)
      .bg(t.popover).border_1().border_color(t.border).rounded(8).shadow_lg()
      .when(!!open, (el) => el.child(item("cs-menu-open", open, true, (cx) => { this.menu = null; this.choose(s, cx); })))
      .child(item("cs-menu-delete", text.menuDelete, !s.running, () => this.askDelete(s), t.blocked))
      .when(s.running, (el) => el.child(div().px(10).pb(4).text_size(11).text_color(t.dim).child(text.menuOpen)));
  }

  renderConfirm(t, text) {
    const c = this.confirm;
    if (!c) return null;
    const button = (id, label, bg, fg, border, action) => h_flex().id(id).h(32).px(14).items_center().rounded(8)
      .border_1().border_color(border).bg(bg).text_color(fg)
      .when(!c.busy, (el) => el.cursor_pointer().hover((st) => st.opacity(0.88)))
      .on_click((_e, cx) => { if (!c.busy) action(cx); cx.notify(); })
      .child(label);
    const card = v_flex().id("cs-confirm").w(480).p(18).gap(10).bg(t.popover).border_1().border_color(t.border).rounded(10).shadow_lg()
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .child(div().text_size(15).font_semibold().text_color(t.foreground).child(text.confirmTitle))
      .child(div().text_color(t.muted).child(text.confirmText))
      .child(h_flex().child(div().px(6).py(2).rounded(5).bg(t.raised).text_size(12).text_color(t.foreground).font_family(settings().font_family ?? "JetBrains Mono").child(c.s.id)))
      .child(div().text_color(t.foreground).child(`« ${c.s.title ?? ""} » ?`))
      .child(div().text_size(11.5).text_color(t.dim).child(text.confirmNote))
      .when(!!c.error, (el) => el.child(div().text_size(12).text_color(t.blocked).child(c.error)))
      .child(h_flex().gap(8).justify_end().pt(4)
        .child(button("cs-no", text.cancel, t.popover, t.foreground, t.input, () => this.cancelDelete()))
        .child(button("cs-yes", c.busy ? text.removing : text.remove, t.blocked, "#ffffff", t.blocked, (cx) => this.doDelete(cx))));
    return div().absolute().inset_0().bg("#00000088").rounded(10).flex().items_center().justify_center()
      .on_mouse_down("left", (_e, cx) => { cx.stop_propagation(); if (!c.busy) { this.cancelDelete(); cx.notify(); } })
      .child(card);
  }

  rows() {
    const words = this.filter.toLowerCase().split(/\s+/).filter(Boolean);
    if (!words.length) return this.sessions ?? [];
    return (this.sessions ?? []).filter((s) => {
      const hay = [s.title, s.project, s.cwd, s.branch, s.first, s.prompt].join(" ").toLowerCase();
      return words.every((w) => hay.includes(w));
    });
  }

  choose(s, _cx) {
    if (!s) return;
    if (s.running) {
      if (!s.terminal) return; // ouverte hors de Herdr : ne pas la dédoubler
      this.close();
      run("agent.focus", { terminal: s.terminal });
      return;
    }
    this.close();
    const argv = ["claude", "--resume", s.id];
    const name = [...(s.title ?? "")].length > 32 ? [...s.title].slice(0, 31).join("") + "…" : s.title;
    const space = this.spaceFor(s.cwd);
    if (space) run("tab.new", { space: space.id, folder: s.cwd, argv, name });
    else run("space.new", { folder: s.cwd, machine: "", argv, tab: name });
  }

  // L'espace où reprendre : celui d'un terminal ouvert dans ce dossier, sinon
  // celui dont les nouveaux terminaux démarrent là (sur cette machine).
  spaceFor(cwd) {
    const clean = (f) => (f ?? "").replace(/\/+$/, "");
    const local = spaces().filter((p) => !p.machine);
    const pane = panes().find((p) => p.terminal && clean(p.cwd) === clean(cwd) && local.some((sp) => sp.tabs.some((tb) => tb.id === p.tab)));
    if (pane) return local.find((sp) => sp.tabs.some((tb) => tb.id === pane.tab));
    return local.find((sp) => clean(sp.folder) === clean(cwd));
  }

  row(t, text, s, i) {
    const on = i === this.at;
    const lost = s.running && !s.terminal;
    const details = [s.project, s.branch, text.prompts(s.prompts)].filter(Boolean).join("  ·  ");
    const badge = s.running
      ? div().flex_none().px(6).py(1).rounded(5).text_size(10.5)
          .bg(lost ? t.raised : t.accent).text_color(lost ? t.muted : t.accent_foreground)
          .child(lost ? text.elsewhere : text.open)
      : null;
    return v_flex()
      .id(`cs-${s.id}`)
      .flex_none()
      .h(ROW)
      .justify_center()
      .mx(4)
      .px(10)
      .gap(2)
      .rounded(7)
      .cursor_pointer()
      .when(on, (el) => el.bg(t.hover))
      .hover((st) => st.bg(t.hover))
      .on_click((_e, cx) => {
        this.at = i;
        this.choose(s, cx);
      })
      .on_mouse_down("right", (e, cx) => {
        this.at = i;
        this.menu = { s, at: e.position, x: null, y: null };
        this.placeMenu();
        cx.notify();
      })
      .child(
        h_flex().gap(8).items_center()
          .child(div().flex_1().min_w(0).truncate().text_color(lost ? t.muted : t.foreground).child(s.title ?? s.id))
          .when(!!badge, (el) => el.child(badge))
          .child(div().flex_none().text_size(11).text_color(t.dim).child(when(s.updated, this.lang))),
      )
      .child(
        h_flex().gap(8).items_center().text_size(11.5).text_color(t.dim)
          .child(div().flex_none().max_w(260).truncate().child(details))
          .when(!!s.prompt && s.prompt !== s.title, (el) =>
            el.child(div().flex_1().min_w(0).truncate().text_color(t.muted).child(`« ${s.prompt} »`))),
      );
  }

  render() {
    const t = theme();
    const text = TEXTS[this.lang];
    const rows = this.rows();
    this.at = Math.max(0, Math.min(this.at, rows.length - 1));
    const sel = rows[this.at];
    const all = this.sessions?.length ?? 0;

    let body;
    if (this.sessions === null) {
      body = h_flex().px(14).py(10).gap(8).items_center().text_color(t.muted)
        .child(svg("mods/workspace-chrome/spinner.svg").size(13).text_color(t.working).spin(900))
        .child(text.loading);
    } else if (this.error) {
      body = v_flex().px(14).py(10).gap(4)
        .child(div().text_color(t.blocked).child(text.error))
        .child(div().text_size(11.5).text_color(t.dim).child(this.error));
    } else if (!rows.length) {
      body = div().px(14).py(10).text_color(t.muted).child(all ? text.none : text.empty);
    } else {
      body = v_flex()
        .id("cs-list")
        .h(Math.min(LIST_MAX, rows.length * ROW))
        .flex_none()
        .overflow_y_scrollbar()
        .track_scroll(this.scroll)
        .children(rows.map((s, i) => this.row(t, text, s, i)));
    }

    const hint = !sel ? "" : sel.running ? (sel.terminal ? text.show : "") : text.resume;
    return v_flex()
      .id("claude-sessions")
      .track_focus(this.handle)
      .relative()
      .w_full()
      .when(!!this.confirm, (el) => el.min_h(300))
      .p(18)
      .gap(10)
      .bg(t.popover)
      .text_size(13)
      .on_size_change((size, cx) => {
        this.size = { width: size.width / (settings().zoom || 1), height: size.height / (settings().zoom || 1) };
        cx.notify();
      })
      .on_mouse_down("right", (e, cx) => {
        if (e.local_position) this.origin = { x: e.position.x - e.local_position.x, y: e.position.y - e.local_position.y };
        this.placeMenu();
        cx.notify();
      })
      .on_mouse_down("left", (e, cx) => {
        if (e.local_position) this.origin = { x: e.position.x - e.local_position.x, y: e.position.y - e.local_position.y };
        if (this.menu) {
          this.menu = null;
          cx.notify();
        }
      })
      .on_key_down((e, cx) => {
        const n = rows.length;
        if (this.confirm) {
          if (e.key === "escape" && !this.confirm.busy) this.cancelDelete();
          else if (e.key === "enter") this.doDelete(cx);
          else return;
          cx.stop_propagation();
          cx.notify();
          return;
        }
        if (this.menu && e.key === "escape") {
          this.menu = null;
          cx.stop_propagation();
          cx.notify();
          return;
        }
        if (e.key === "escape") return this.close();
        if (!n) return;
        if (e.key === "down") this.at = (this.at + 1) % n;
        else if (e.key === "up") this.at = (this.at + n - 1) % n;
        else if (e.key === "pagedown") this.at = Math.min(n - 1, this.at + 8);
        else if (e.key === "pageup") this.at = Math.max(0, this.at - 8);
        else return;
        this.scroll.scroll_to_item(this.at);
        cx.stop_propagation();
        cx.notify();
      })
      .child(
        h_flex().items_center().gap(10)
          .child(div().text_size(15).font_semibold().text_color(t.foreground).child(text.title))
          .child(div().flex_1().text_size(11.5).text_color(t.dim).child(this.sessions ? text.count(rows.length, all) : ""))
          .child(div().text_size(11).text_color(t.dim).child(hint))
          .child(
            div().id("cs-esc").px(6).py(2).rounded(5).text_size(11).text_color(t.dim).cursor_pointer()
              .hover((s) => s.bg(t.hover).text_color(t.foreground))
              .on_click(() => this.close())
              .child("Esc"),
          ),
      )
      .child(
        h_flex().h(36).flex_none().px(10).gap(8).items_center().rounded(9).border_1().border_color(t.accent).bg(t.background)
          .child(svg("mods/workspace-chrome/search.svg").size(15).text_color(t.dim))
          .child(this.input ? Input.new(this.input).flex_1().h_full().text_size(12.8).text_color(t.foreground) : div().flex_1()),
      )
      .child(body)
      .when(!!this.menu, (el) => el.child(this.renderMenu(t, text)))
      .when(!!this.confirm, (el) => el.child(this.renderConfirm(t, text)));
  }
}

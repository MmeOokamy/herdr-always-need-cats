// pane-cats:
// Herdr's pane header (the "pane" mod 0.1.15, Apache-2.0), where the agent's cat
// jumps in when it is waiting for you or has finished: the header takes a tint (orange, green), the cat hops with its
// bubble (what strip-cats says, shared "strip-cats.live"). Click: the pane. Setting in the cats menu:
// "strip-cats.header". Files dropped on an agent's header are passed to it as @ mentions by
// the cats strip (shared "strip-cats.drop"). The coat is the one from agents-cats and strip-cats.
// The rest is Herdr's.
//
// A pane's header, for layouts that frame their panes:
//   { "tab": "active", "pane": { "header": { "content": { "mod": "pane" } } } }
// Shows the program's icon (the app's program table), the agent's name or
// the terminal's title, the folder, and the agent's status; buttons split, zoom and close
// this pane. Props from the app: { pane, terminal }. Click: focus the pane.

import { View, div, svg, image } from "gpui-kit";
import { h_flex } from "gpui-base";
import { panes, props, run, theme, home, layout, shared, setShared, appHome, readTextFile } from "herdr";

// Match the first visible tab frame, including the active child of a stack.
function paneFrame(node) {
  if (!node || node.hidden) return null;
  if (node.content?.tab && node.content.pane) return node.content.pane;
  let children = node.children ?? [];
  if (node.type === "stack") {
    const visible = children.filter(child => !child.hidden);
    children = [visible.find(child => child.id === node.active) ?? visible[0]];
  }
  for (const child of children) {
    const frame = paneFrame(child);
    if (frame) return frame;
  }
  return null;
}

const COATS = ["ginger", "grey", "black", "cream", "brown", "blue"];
const NEEDS_YOU = { fr: "A besoin de toi", en: "Needs you" };

// Like agents-cats: picked in the strip's menu, otherwise derived from the terminal's address.
function coatOf(address) {
  const picked = shared("strip-cats")?.terminals?.[address];
  if (COATS.includes(picked)) return picked;
  let h = 0;
  for (const c of address) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return COATS[h % COATS.length];
}
const LOUD = { blocked: "blocked", done: "done", finished: "done" };
const on = (key) => shared(key) !== false;
const tint = (c, a) => (/^#[0-9a-f]{6}$/i.test(c ?? "") ? c + a : c);

function icon(p, size, color) {
  if (!p?.icon) return null;
  return p.tint ? svg(p.icon).size(size).flex_none().text_color(color) : image(p.icon).w(size).h(size).flex_none();
}

function folder(cwd) {
  if (!cwd) return "";
  const h = home();
  return cwd === h ? "~" : cwd.startsWith(h + "/") ? "~" + cwd.slice(h.length) : cwd;
}

export default class Pane extends View {
  init(_props, cx) {
    this.hovered = false;
    this.lang = "fr";
    cx.spawn(async (cx) => {
      try {
        // The mod folder is a link to the clone: config.json sits next to it.
        const data = JSON.parse((await readTextFile(`${appHome()}/mods/pane-cats/../config.json`)) ?? "{}");
        const lang = String(data?.lang ?? "fr").toLowerCase();
        if (NEEDS_YOU[lang]) this.lang = lang;
      } catch {
        // no config: French
      }
      cx.notify();
    });
  }

  me() {
    return panes().find((p) => p.pane === props()?.pane);
  }

  button(t, id, icon, command, args) {
    return div()
      .id(id)
      .p(3)
      .rounded(4)
      .text_color(t.dim)
      .hover((s) => s.bg(t.hover).text_color(t.foreground))
      .on_click((_e, cx) => {
        cx.stop_propagation();
        run(command, args);
      })
      .child(svg(`mods/pane-cats/${icon}.svg`).size(14));
  }

  // The cat that jumps into the header, and its bubble.
  cat(t, p) {
    const live = p.terminal && shared("strip-cats.live")?.[p.terminal];
    const mood = live?.mood;
    if (!LOUD[mood] || !on("strip-cats.header")) return null;
    const coat = coatOf(p.terminal);
    const color = t[LOUD[mood]];
    const gif = mood === "blocked" ? "question" : mood === "done" ? "done" : "meow";
    const pane = p.pane;
    return { color, el: h_flex().flex_1().min_w(0).gap(6).items_center()
      .child(div().id(`cat-hop-${pane}`).relative().flex_none().w(24).h(28)
        .child(image(`mods/strip-cats/img/cat-${coat}-${gif}.gif`).absolute().left(0).top(1).w(24).h(27)
          .id(`cat-img-${pane}`).loop("top", { from: 2, to: mood === "blocked" ? -3 : 0, period: mood === "blocked" ? 520 : 800 })))
      .child(div().flex_1().min_w(0).truncate().font_semibold().text_color(color).child(live.text)) };
  }

  render(cx) {
    const t = theme();
    const p = this.me();
    if (!p) return div();
    const name = ((p.program?.agent || p.program?.shell) && p.program.name) || p.title || p.program?.name || "shell";
    const pic = icon(p.program, 14, t.dim);
    const st = p.status;
    const pane = p.pane;
    const bottom = paneFrame(layout())?.header?.position === "bottom";
    const cat = this.cat(t, p);
    return h_flex()
      .id(`pane-head-${pane}`)
      .size_full()
      .px(10)
      .gap(8)
      .items_center()
      .bg(cat ? tint(cat.color, "22") : t.background)
      .when(bottom, el => el.border_t(1))
      .when(!bottom, el => el.border_b(1))
      .border_color(t.border)
      .text_size(12)
      .on_hover((hovered, cx) => { this.hovered = hovered; cx.notify(); })
      .on_click(() => run("pane.focus", { pane }))
      .on_drop((e) => {
        if (p.terminal && (p.status || p.program?.agent) && e.paths?.length)
          setShared("strip-cats.drop", { id: `${Date.now()}-${pane}`, address: p.terminal, pane, paths: e.paths });
      })
      .when(Boolean(pic), (el) => el.child(pic))
      .child(div().flex_none().truncate().max_w(260).font_medium().text_color(t.foreground).child(name))
      .when(!cat, (el) => el.child(div().flex_1().truncate().text_color(t.dim).child(folder(p.cwd))))
      .when(!!cat, (el) => el.child(cat.el))
      .when(st === "working", el => el.child(svg("mods/workspace-chrome/spinner.svg").size(12).flex_none().text_color(t.working).spin(900)))
      .when(st === "blocked", el => el.child(div().flex_none().px(6).h(18).flex().items_center().rounded(5).bg(t.blocked + "26").text_size(10.5).font_semibold().text_color(t.blocked).child(NEEDS_YOU[this.lang])))
      .when(st === "done", el => el.child(div().size(7).flex_none().rounded(4).bg(t.done)))
      .when(this.hovered, el => el
        .child(this.button(t, `ph-r-${pane}`, "split-right", "pane.split", { direction: "right", pane }))
        .child(this.button(t, `ph-d-${pane}`, "split-down", "pane.split", { direction: "down", pane }))
        .child(this.button(t, `ph-z-${pane}`, p.zoomed ? "unzoom" : "zoom", "pane.zoom", { pane }))
        .child(this.button(t, `ph-x-${pane}`, "close", "pane.close", { pane })));
  }
}

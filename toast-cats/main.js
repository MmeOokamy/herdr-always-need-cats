// toast-cats: Herdr notifications, with a cat for agents.
//
// Replaces the "toast" mod of Herdr 0.1.15 (upstream-toast-0.1.15.js.txt), selected
// by the "toast" key of the layout. When a notification is about a Claude
// Code agent (it has finished, or it needs you), it takes the shape of the
// we-always-need-cats cats: a bubble above the agent's cat, with the same coat
// as in the agent list (agents-cats), which jumps for joy when it has
// finished and meows when it is waiting. Other notifications keep their
// original look.
//
// Like the original: a click runs the notification's action (show the
// agent) and closes it; Herdr closes it on its own after a few seconds.

import { View, div, image } from "gpui-kit";
import { v_flex, h_flex } from "gpui-base";
import { agents, appHome, closeOverlay, props, readTextFile, run, shared, theme } from "herdr";

const DOT = { error: "blocked", warning: "working", success: "done", info: "accent" };

// Same coats and same choice as agents-cats and strip-cats: an agent keeps its cat.
const CAT_COATS = ["ginger", "grey", "black", "cream", "brown", "blue"];
const isClaude = (p) => p?.app === "claude-code" || p?.program?.key === "claude" || /claude/i.test(p?.program?.name ?? "");
function coatOf(address) {
  const picked = shared("strip-cats")?.terminals?.[address]; // picked in the strip menu
  if (CAT_COATS.includes(picked)) return picked;
  let h = 0;
  for (const c of address) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return CAT_COATS[h % CAT_COATS.length];
}

// Colors of the we-always-need-cats cats.
const OUTLINE = "#2B2230";
const CREAM = "#FFFDF5";
const BORDER = { done: "#2F9E44", blocked: "#E8590C" };
const ANIMATION = { done: "done", blocked: "question" };

const CAT_W = 55; // image generated at 176 x 160
const CAT_H = 50;

const TEXTS = {
  fr: { done: "a fini", blocked: "a besoin de toi" },
  en: { done: "done", blocked: "needs you" },
};

// The agent the notification is about. Herdr's have the title
// "Claude Code finished" or "... needs you", the body "<space> / <tab>" and
// the action { name: "agent.focus", args: { terminal: "t1" } }. Without
// arguments, the last agent to have finished or to be waiting.
function agentOf(p) {
  const list = agents() ?? [];
  const args = p.action?.args ?? {};
  const keys = [args.terminal, args.address, args.agent, args.pane].filter(Boolean);
  const named = list.find((a) => keys.includes(a.address) || keys.includes(a.pane));
  if (named) return named;
  if (!p.action?.name || !/^(agent|pane|terminal)\./.test(p.action.name)) return null;
  const waiting = list.filter((a) => a.status === "done" || a.status === "blocked");
  return waiting.sort((a, b) => b.seq - a.seq)[0] ?? null;
}

export default class Toast extends View {
  init(_props, cx) {
    this.lang = "fr";
    // The mod folder is a link to the clone: config.json sits next to it.
    cx.spawn(async (cx) => {
      try {
        const data = JSON.parse((await readTextFile(`${appHome()}/mods/toast-cats/../config.json`)) ?? "{}");
        if (data?.lang) this.lang = String(data.lang).toLowerCase();
      } catch (_e) {
        // no config: French
      }
      cx.notify();
    });
  }

  click(p) {
    if (p.action?.name) run(p.action.name, p.action.args ?? {});
    closeOverlay(p.overlay);
  }

  render(cx) {
    const p = props() ?? {};
    const agent = agentOf(p);
    if (agent && isClaude(agent)) return this.cat(p, agent);
    return this.plain(p);
  }

  // --- Agent cat -----------------------------------------------------------

  cat(p, agent) {
    const needs = agent.status === "blocked" || /needs you/i.test(p.title ?? "");
    const state = needs ? "blocked" : "done";
    const text = TEXTS[this.lang] ?? TEXTS.fr;
    // Like the session cats: the project, then what is happening.
    const tab = /^\d+$/.test(agent.tab_name ?? "") ? "" : ` / ${agent.tab_name}`;
    const project = agent.space_name ? `${agent.space_name}${tab}` : p.body || "Claude Code";
    const line = agent.title ? `${text[state]} : ${agent.title}` : text[state];
    const sprite = `mods/agents-cats/sprites/${coatOf(agent.address)}-${ANIMATION[state]}.webp`;
    // A notification's height is set by Herdr (about 64 px):
    // the cat on the left, its bubble on the right.
    const bubble = v_flex()
      .flex_1()
      .min_w(0)
      .px(9)
      .py(4)
      .rounded(7)
      .border(2)
      .border_color(BORDER[state])
      .bg(CREAM)
      .text_color(OUTLINE)
      .child(div().truncate().font_semibold().text_size(13).child(project))
      .child(div().truncate().text_size(12).child(line));
    return h_flex()
      .id("toast")
      .size_full()
      .pl(4)
      .pr(10)
      .gap(6)
      .items_center()
      .cursor_pointer()
      .on_click(() => this.click(p))
      .child(image(sprite).w(CAT_W).h(CAT_H).flex_none())
      .child(bubble);
  }

  // --- Other notifications: the original toast -----------------------------

  plain(p) {
    const t = theme();
    const login = /^([a-z0-9][a-z0-9_.-]{0,31}) needs login; run hc machine login \1$/.exec(p.body ?? "");
    const command = login ? `hc machine login ${login[1]}` : null;
    return h_flex()
      .id("toast")
      .size_full()
      .px(18)
      .gap(12)
      .items_center()
      .bg(t.popover)
      .cursor_pointer()
      .hover((s) => s.bg(t.hover))
      .on_click(() => this.click(p))
      .child(p.icon ? image(p.icon).w(18).h(18).flex_none() : div().size(8).rounded(4).flex_none().bg(t[DOT[p.level] ?? "accent"]))
      .child(
        v_flex()
          .flex_1()
          .overflow_hidden()
          .child(div().truncate().font_semibold().text_size(13).text_color(t.foreground).child(login ? `${login[1]} needs a login: run` : p.title ?? ""))
          .when(!login && Boolean(p.body), (el) => el.child(div().truncate().text_size(12).text_color(t.muted).child(p.body ?? "")))
          .when(Boolean(login), (el) => el.child(h_flex().gap(8).items_center()
            .child(div().flex_1().min_w(0).truncate().tooltip(command).text_size(12).text_color(t.muted).child(command))
            .child(div().id("toast-login-copy").flex_none().px(6).py(3).rounded(4).bg(t.raised)
              .text_size(12).text_color(t.foreground).cursor_pointer().hover(s => s.bg(t.hover))
              .on_click((_e, cx) => { cx.stop_propagation(); cx.write_to_clipboard(command); this.copied = true; cx.notify(); })
              .child(this.copied ? "Copied" : "Copy")))),
      );
  }
}

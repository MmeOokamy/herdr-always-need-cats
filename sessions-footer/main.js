// sessions-footer : le pied de la barre latérale (bloc sidebar-footer du
// layout main-usage-cat), repris du mode footer du mod workspace-chrome de
// Herdr 0.1.15, avec une ligne « sessions » sous Settings, qui ouvre la
// liste des sessions Claude (mod claude-sessions).

import { View, div, svg } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { layout, run, theme, updates } from "herdr";

function find(node, id) {
  if (node?.id === id) return node;
  for (const child of node?.children ?? []) {
    const found = find(child, id);
    if (found) return found;
  }
  return null;
}

// Barre latérale repliée en rail : selon sa largeur, comme workspace-chrome.
const narrow = () => (find(layout(), "sidebar")?.size?.px ?? Infinity) < 160;

export default class SessionsFooter extends View {
  render() {
    const t = theme();
    const collapsed = narrow();
    const row = (id, icon, label, dim, action) => h_flex().id(id).h(28).px(8).gap(9).items_center().rounded(8)
      .when(collapsed, (el) => el.relative().w(32).px(0).justify_center().tooltip(label))
      .text_color(dim ? t.dim : t.muted).hover((s) => s.bg(t.hover).text_color(t.foreground)).cursor_pointer()
      .on_click(action).child(svg(icon).size(14))
      .when(!collapsed, (el) => el.child(label));
    const ready = div().size(6).rounded_full().bg(t.accent);
    return v_flex().size_full().bg(t.chrome).border_t(1).border_color(t.border).px(8).pt(4).pb(8).text_size(13)
      .when(collapsed, (el) => el.px(0).items_center())
      .child(row("settings", "mods/workspace-chrome/settings.svg", "Settings", false, () => run("app.settings"))
        .when(Boolean(updates().app.ready), (el) => el.child(collapsed ? ready.absolute().top(5).right(6) : ready)))
      .child(row("sessions", "mods/sessions-footer/cat.svg", "sessions", false, () => run("mod.open", { name: "claude-sessions" })))
      .child(row("machine", "mods/workspace-chrome/plus.svg", "Add machine", true, () => run("mod.open", { name: "machine-add" })));
  }
}

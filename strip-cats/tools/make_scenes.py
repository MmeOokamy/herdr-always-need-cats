#!/usr/bin/env python3
"""Draws the backgrounds of the "cats-strip" mod: rooms and places where the cats stroll.

    python3 make_scenes.py            # writes ../scenes/<id>.png

Each background is drawn in pixel art at 640 × 38 drawing pixels, then enlarged 3 times
(same scale as the cats: 3 screen px per drawing pixel) and repeated twice in
width, i.e. 3840 × 114 px. The floor takes the last 8 lines: the cats walk on it.
The left and right edges match up, so that the repetition does not show.
Requires Pillow. Original drawings, MIT license like the rest of the repository.
"""

import os
import random

from PIL import Image, ImageDraw

W, H = 640, 38
FLOOR = 30  # first line of the floor
SCALE = 3
REPEAT = 2
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scenes")


class Pic:
    def __init__(self, bg):
        self.im = Image.new("RGB", (W, H), bg)
        self.d = ImageDraw.Draw(self.im)

    def r(self, x, y, w, h, c):
        """Filled rectangle; x may go past the frame, it is then wrapped (edges match up)."""
        if w <= 0 or h <= 0:
            return
        for dx in (0, -W, W):
            x0 = x + dx
            if x0 + w <= 0 or x0 >= W:
                continue
            self.d.rectangle([x0, y, x0 + w - 1, y + h - 1], fill=c)

    def p(self, x, y, c):
        if 0 <= y < H:
            self.im.putpixel((x % W, y), rgb(c) if isinstance(c, str) else c)

    def disc(self, cx, cy, rad, c):
        for y in range(cy - rad, cy + rad + 1):
            for x in range(cx - rad, cx + rad + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad + rad * 0.6:
                    self.p(x, y, c)

    def hline(self, x, y, w, c):
        self.r(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.r(x, y, 1, h, c)

    def frame(self, x, y, w, h, c):
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def save(self, name):
        big = self.im.resize((W * SCALE, H * SCALE), Image.NEAREST)
        out = Image.new("RGB", (W * SCALE * REPEAT, H * SCALE))
        for i in range(REPEAT):
            out.paste(big, (i * W * SCALE, 0))
        os.makedirs(OUT, exist_ok=True)
        out.save(os.path.join(OUT, f"{name}.png"), optimize=True)


# --- shared elements ---------------------------------------------------------------

def planks(s, rnd, base, line, light, y0=FLOOR, rows=(4, 4)):
    """Parquet floor: boards offset from one row to the next."""
    y = y0
    for rh in rows:
        s.r(0, y, W, rh, base)
        s.hline(0, y, W, light)
        x = rnd.randrange(0, 30)
        while x < W:
            s.vline(x, y, rh, line)
            x += rnd.randrange(22, 46)
        y += rh
    s.hline(0, y0, W, line)


def window(s, x, y, w, h, sky, frame="#e8dcc8", night=False, rnd=None):
    s.r(x - 1, y - 1, w + 2, h + 2, frame)
    # the sky, in bands
    for i in range(h):
        t = i / max(1, h - 1)
        c = mix(sky[0], sky[1], t)
        s.hline(x, y + i, w, c)
    if night and rnd:
        for _ in range(w * h // 18):
            s.p(x + rnd.randrange(w), y + rnd.randrange(h), "#f4eecf")
    elif not night:
        # a cloud
        cx = x + w // 3
        s.r(cx, y + 4, 9, 2, "#f3f7fa")
        s.r(cx + 2, y + 3, 5, 1, "#f3f7fa")
    s.vline(x + w // 2, y, h, frame)
    s.hline(x, y + h // 2, w, frame)
    s.r(x - 2, y + h + 1, w + 4, 2, mix(frame, "#000000", 0.15))  # sill


def curtains(s, x, y, w, h, c, dark):
    for side in (x - 5, x + w + 1):
        s.r(side, y - 3, 5, h + 6, c)
        s.vline(side + 2, y - 2, h + 5, dark)
    s.r(x - 7, y - 4, w + 14, 1, "#3a2d24")  # curtain rod


def books(s, rnd, x, y, w, h):
    colors = ["#b0413e", "#3f6e8c", "#d9a441", "#4f8a5b", "#7a4f8c", "#c96f3b", "#e2d2b0", "#2f4f6f"]
    cx = x
    while cx < x + w - 1:
        bw = rnd.choice((1, 2, 2, 3))
        bh = rnd.randrange(max(2, h - 3), h + 1)
        if cx + bw > x + w:
            break
        s.r(cx, y + h - bh, bw, bh, rnd.choice(colors))
        cx += bw
        if rnd.random() < 0.12:
            cx += 1


def bookshelf(s, rnd, x, y, w, h, wood="#5a3b26", back="#3b2618"):
    s.r(x, y, w, h, wood)
    shelves = 3
    inner = (h - 2) // shelves
    for i in range(shelves):
        sy = y + 1 + i * inner
        s.r(x + 1, sy, w - 2, inner - 1, back)
        books(s, rnd, x + 2, sy + 1, w - 4, inner - 2)


def plant(s, x, y_floor, pot="#b5653a", leaf="#3f8a4a", light="#57a35c", tall=12):
    s.r(x, y_floor - 7, 9, 7, pot)
    s.r(x - 1, y_floor - 8, 11, 2, mix(pot, "#000000", 0.2))
    top = y_floor - 8 - tall
    for i, (dx, dy, rad) in enumerate(((4, tall - 3, 3), (1, tall - 7, 3), (7, tall - 6, 3), (4, tall - 10, 3), (0, tall - 2, 2), (9, tall - 3, 2))):
        s.disc(x + dx, top + dy, rad, leaf if i % 2 else light)
    s.vline(x + 4, y_floor - 8 - 4, 4, "#2f6b3a")


def yarn(s, x, y, c, dark):
    s.disc(x, y, 2, c)
    s.p(x - 1, y - 1, dark)
    s.p(x + 1, y, dark)
    s.hline(x + 2, y + 2, 4, c)


def cat_bed(s, x, y_floor, c="#9c4f5f", inner="#e8c9b0"):
    s.r(x, y_floor - 4, 18, 4, c)
    s.r(x + 2, y_floor - 5, 14, 2, inner)
    s.r(x - 1, y_floor - 3, 20, 3, mix(c, "#000000", 0.2))


def mix(a, b, t):
    a, b = rgb(a), rgb(b)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rgb(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


# --- the backgrounds ---------------------------------------------------------------

def salon():
    rnd = random.Random(1)
    s = Pic("#6d5a7a")
    for x in range(0, W, 8):  # striped wallpaper
        s.r(x, 0, 3, FLOOR, "#655270")
    for x in range(4, W, 8):
        for y in range(3, FLOOR - 4, 6):
            s.p(x + 1, y, "#7e6a8b")
    s.r(0, FLOOR - 3, W, 3, "#3d3247")  # baseboard
    s.hline(0, FLOOR - 3, W, "#8a7896")
    planks(s, rnd, "#7a5232", "#5e3d24", "#8c6040")
    # rug
    s.r(96, FLOOR + 3, 104, 3, "#9c3f3f")
    for x in range(98, 198, 4):
        s.p(x, FLOOR + 4, "#e0b25a")
    # window and curtains
    window(s, 40, 5, 34, 16, ("#8ec5e8", "#cfe8f5"))
    curtains(s, 40, 5, 34, 16, "#b0413e", "#8c2f2d")
    # sofa
    s.r(108, 13, 72, 10, "#3f6e8c")
    s.hline(108, 13, 72, "#5687a6")
    s.r(104, 17, 6, 10, "#355e78")
    s.r(178, 17, 6, 10, "#355e78")
    s.r(110, 21, 68, 6, "#4a7d9c")
    for x in (112, 135, 158):
        s.r(x, 15, 18, 6, "#d9a441" if x != 135 else "#c96f3b")
    s.vline(107, 27, 3, "#2a2a2a")
    s.vline(181, 27, 3, "#2a2a2a")
    # floor lamp
    s.vline(195, 9, 20, "#2d2d33")
    s.r(192, FLOOR - 1, 7, 1, "#2d2d33")
    s.r(191, 4, 9, 2, "#f2d48a")
    s.r(190, 6, 11, 3, "#e8c46f")
    # plant
    plant(s, 214, FLOOR)
    # picture frames
    s.r(250, 6, 18, 13, "#c9a24a")
    s.r(252, 8, 14, 9, "#8ec5e8")
    s.r(252, 13, 14, 4, "#5c9a46")
    s.disc(262, 10, 1, "#f2d48a")
    s.r(274, 9, 10, 10, "#3a2d24")
    s.r(276, 11, 6, 6, "#d9a441")
    # bookcase
    bookshelf(s, rnd, 316, 4, 40, 26)
    # radiator
    s.r(376, 19, 26, 8, "#cfd3d6")
    for x in range(378, 402, 3):
        s.vline(x, 19, 8, "#aeb4b9")
    # clock
    s.disc(425, 9, 4, "#f1eadb")
    s.vline(425, 6, 3, "#2d2d33")
    s.hline(425, 9, 3, "#2d2d33")
    # armchair and side table
    s.r(440, 12, 26, 9, "#8c3b3b")
    s.r(437, 16, 5, 11, "#7a3232")
    s.r(464, 16, 5, 11, "#7a3232")
    s.r(441, 20, 24, 7, "#9c4646")
    s.vline(440, 27, 3, "#2a2a2a")
    s.vline(466, 27, 3, "#2a2a2a")
    s.r(478, 19, 14, 2, "#5a3b26")
    s.vline(484, 21, 9, "#5a3b26")
    s.r(481, 16, 4, 3, "#f1eadb")  # cup
    # second window
    window(s, 512, 5, 30, 16, ("#8ec5e8", "#cfe8f5"))
    curtains(s, 512, 5, 30, 16, "#b0413e", "#8c2f2d")
    # basket and yarn ball
    cat_bed(s, 572, FLOOR + 2)
    yarn(s, 604, FLOOR + 3, "#4f8ac9", "#3a6ea8")
    return s


def cuisine():
    rnd = random.Random(2)
    s = Pic("#c9b99a")
    # wall tiles
    s.r(0, 11, W, 10, "#e4e0d6")
    for x in range(0, W, 4):
        s.vline(x, 11, 10, "#c7c1b3")
    for y in range(11, 21, 4):
        s.hline(0, y, W, "#c7c1b3")
    # checkered floor
    for y in range(FLOOR, H, 4):
        for x in range(0, W, 4):
            s.r(x, y, 4, 4, "#d6d0c4" if (x // 4 + y // 4) % 2 else "#8f8778")
    s.hline(0, FLOOR, W, "#5e574c")
    # high and low cabinets, worktop (except at the fridge and the table)
    def run(x0, x1):
        s.r(x0, 1, x1 - x0, 10, "#6f8f6a")
        s.r(x0, 21, x1 - x0, 2, "#8a6a4a")
        s.r(x0, 23, x1 - x0, FLOOR - 23, "#6f8f6a")
        for x in range(x0, x1 - 1, 16):
            s.frame(x + 1, 2, 15, 8, "#5c7a58")
            s.frame(x + 1, 24, 15, FLOOR - 25, "#5c7a58")
            s.r(x + 13, 5, 1, 2, "#d9d4c4")
            s.r(x + 13, 26, 1, 2, "#d9d4c4")
    run(0, 160)
    run(208, 352)
    # sink and tap
    s.r(40, 21, 22, 2, "#aeb4b9")
    s.vline(50, 16, 5, "#aeb4b9")
    s.hline(50, 16, 4, "#aeb4b9")
    # hob and saucepan, steam
    s.r(100, 20, 24, 1, "#2d2d33")
    s.r(104, 15, 14, 5, "#b0413e")
    s.hline(102, 15, 18, "#8c2f2d")
    for i, y in enumerate(range(8, 14, 2)):
        s.p(108 + (i % 2), y, "#f3f3f3")
        s.p(113 - (i % 2), y + 1, "#f3f3f3")
    # oven
    s.r(98, 24, 28, 5, "#2d2d33")
    s.r(101, 25, 22, 3, "#f2a04b")
    # fridge
    s.r(162, 1, 26, FLOOR - 1, "#e6e9ec")
    s.hline(162, 11, 26, "#b8bec4")
    s.vline(185, 4, 5, "#9aa1a8")
    s.vline(185, 14, 8, "#9aa1a8")
    for x, c in ((166, "#d9a441"), (172, "#b0413e"), (168, "#4f8ac9")):
        s.r(x, 15 + (x % 3), 3, 3, c)  # magnets
    # window and herbs
    window(s, 222, 3, 34, 15, ("#8ec5e8", "#cfe8f5"))
    for x in (226, 236, 246):
        s.r(x, 19, 6, 2, "#b5653a")
        s.disc(x + 3, 17, 2, "#4f8a5b")
    # jars and hanging utensils
    for x, c in ((270, "#d9a441"), (277, "#c96f3b"), (284, "#e2d2b0")):
        s.r(x, 16, 5, 5, c)
        s.hline(x, 16, 5, "#8a6a4a")
    s.hline(296, 13, 40, "#8a6a4a")
    for x in range(300, 334, 8):
        s.vline(x, 13, 5, "#aeb4b9")
        s.r(x - 1, 18, 3, 2, "#aeb4b9")
    # table, chairs, pendant lamp
    s.vline(430, 0, 8, "#2d2d33")
    s.r(424, 8, 13, 3, "#3f6e8c")
    s.r(427, 11, 7, 1, "#f2d48a")
    s.r(395, 18, 72, 2, "#8a6a4a")
    s.vline(398, 20, 10, "#6b4f35")
    s.vline(463, 20, 10, "#6b4f35")
    s.r(416, 15, 6, 3, "#f1eadb")  # fruit basket
    s.disc(436, 15, 2, "#b0413e")
    s.disc(441, 15, 2, "#d9a441")
    for x in (375, 474):
        s.vline(x + (0 if x < 400 else 9), 11, 19, "#6b4f35")
        s.r(x, 22, 10, 2, "#6b4f35")
        s.vline(x + (9 if x < 400 else 0), 22, 8, "#6b4f35")
    # cat bowl
    s.r(520, FLOOR + 1, 10, 3, "#4f8ac9")
    s.r(521, FLOOR, 8, 1, "#c96f3b")
    s.r(534, FLOOR + 1, 10, 3, "#4f8ac9")
    s.r(535, FLOOR, 8, 1, "#8ec5e8")
    # spice rack
    s.r(560, 9, 50, 2, "#8a6a4a")
    for i, x in enumerate(range(562, 606, 6)):
        s.r(x, 4, 4, 5, ("#b0413e", "#d9a441", "#4f8a5b", "#7a4f8c")[i % 4])
    s.r(560, 21, 64, 2, "#8a6a4a")
    s.r(560, 23, 64, FLOOR - 23, "#6f8f6a")
    s.frame(561, 24, 30, FLOOR - 25, "#5c7a58")
    s.frame(592, 24, 31, FLOOR - 25, "#5c7a58")
    return s


def bureau():
    rnd = random.Random(3)
    s = Pic("#3e5a6e")
    for y in range(2, FLOOR - 3, 5):
        for x in range((y // 5) % 2 * 5, W, 10):
            s.p(x, y, "#46657a")
    s.r(0, FLOOR - 2, W, 2, "#2b3f4d")
    # carpet
    s.r(0, FLOOR, W, H - FLOOR, "#5d6270")
    for _ in range(320):
        s.p(rnd.randrange(W), rnd.randrange(FLOOR, H), "#6b7180")
    s.hline(0, FLOOR, W, "#474b57")
    # string lights
    for x in range(0, W, 3):
        y = 2 + int(2 * abs(((x % 40) - 20) / 20))
        s.p(x, y, "#2b2b2b")
    for i, x in enumerate(range(4, W, 12)):
        y = 3 + int(2 * abs(((x % 40) - 20) / 20))
        s.p(x, y, ("#f2d48a", "#e07a7a", "#8ec5e8", "#9ad48a")[i % 4])
    # desk, screen with code, keyboard, lamp
    s.r(30, 18, 70, 2, "#8a6a4a")
    s.vline(32, 20, 10, "#6b4f35")
    s.vline(97, 20, 10, "#6b4f35")
    s.r(80, 20, 17, 9, "#7a5c40")
    s.hline(81, 24, 15, "#6b4f35")
    s.r(46, 5, 30, 12, "#1b1f27")
    s.r(47, 6, 28, 10, "#1e2a36")
    for i, y in enumerate(range(7, 15, 2)):
        x = 49 + (i % 3) * 2
        s.hline(x, y, rnd.randrange(6, 16), ("#8ec5e8", "#d9a441", "#9ad48a", "#e07a7a")[i % 4])
    s.r(59, 16, 4, 2, "#1b1f27")
    s.r(48, 17, 22, 1, "#cfd3d6")
    s.vline(36, 10, 8, "#2d2d33")
    s.r(34, 8, 6, 3, "#d9a441")
    s.r(84, 15, 5, 3, "#f1eadb")  # cup
    # office chair
    s.r(108, 10, 12, 11, "#2d2d33")
    s.r(106, 21, 16, 3, "#2d2d33")
    s.vline(113, 24, 4, "#555")
    s.hline(107, 28, 14, "#555")
    # poster
    s.r(140, 4, 16, 20, "#e2d2b0")
    s.r(142, 6, 12, 10, "#c96f3b")
    s.disc(148, 10, 3, "#f2d48a")
    s.r(142, 17, 12, 1, "#3a2d24")
    s.r(142, 19, 8, 1, "#3a2d24")
    # wall shelf
    for y in (8, 17):
        s.r(176, y, 40, 2, "#8a6a4a")
        books(s, rnd, 178, y - 6, 26, 6)
    s.r(207, 13, 5, 4, "#b5653a")
    s.disc(209, 11, 2, "#4f8a5b")
    # bed
    s.r(240, 9, 4, 21, "#6b4f35")
    s.r(240, 18, 90, 4, "#e9e4d8")
    s.r(252, 20, 78, 6, "#c07a4a")
    s.hline(252, 20, 78, "#d89566")
    s.r(244, 15, 14, 5, "#f3f0e8")
    s.r(240, 26, 92, 2, "#6b4f35")
    s.vline(330, 15, 15, "#6b4f35")
    # window (evening)
    window(s, 360, 5, 30, 15, ("#3b4a7a", "#e0956b"), frame="#cfd3d6")
    # cat tree
    x = 420
    s.vline(x + 6, 6, 24, "#cbb68a")
    s.vline(x + 7, 6, 24, "#b9a375")
    s.vline(x + 26, 14, 16, "#cbb68a")
    s.vline(x + 27, 14, 16, "#b9a375")
    for px, py, pw in ((x, 5, 16), (x + 18, 13, 16), (x, 20, 14), (x - 2, FLOOR - 2, 38)):
        s.r(px, py, pw, 2, "#8a6d55")
        s.hline(px, py, pw, "#a3866c")
    s.vline(x + 30, 15, 6, "#d9a441")  # pompom
    s.disc(x + 30, 22, 1, "#e07a7a")
    # pouf, yarn ball, plant
    s.r(480, 22, 20, 8, "#7a4f8c")
    s.hline(480, 22, 20, "#8f63a1")
    yarn(s, 512, FLOOR + 3, "#e07a7a", "#c05a5a")
    plant(s, 540, FLOOR, pot="#cfd3d6", tall=14)
    # chest of drawers
    s.r(570, 14, 46, 16, "#8a6a4a")
    for y in (16, 21, 26):
        s.r(572, y, 42, 4, "#7a5c40")
        s.r(591, y + 1, 4, 1, "#d9d4c4")
    s.r(582, 8, 10, 6, "#e2d2b0")  # photo frame
    s.r(584, 10, 6, 3, "#8ec5e8")
    return s


def jardin():
    rnd = random.Random(4)
    s = Pic("#8ec5e8")
    for y in range(FLOOR):  # sky
        s.hline(0, y, W, mix("#6fb0e0", "#cfe8f5", y / FLOOR))
    for cx, cy in ((60, 5), (230, 3), (420, 6), (560, 4)):
        s.r(cx, cy + 1, 16, 3, "#f3f7fa")
        s.r(cx + 3, cy, 8, 1, "#f3f7fa")
        s.r(cx + 4, cy - 1, 4, 1, "#f3f7fa")
    # hills in the distance
    for x in range(W):
        h = 4 + int(3 * abs(((x * 3) % 160 - 80) / 80))
        s.vline(x, 18 - h // 2, FLOOR, "#9cc58a")
    # house
    s.r(0, 4, 70, FLOOR - 4, "#a0563f")
    for y in range(5, FLOOR, 3):
        off = 0 if (y // 3) % 2 else 3
        for x in range(off, 70, 6):
            s.vline(x, y, 3, "#8c4a36")
        s.hline(0, y, 70, "#8c4a36")
    s.r(0, 2, 74, 3, "#5a3a35")
    s.r(12, 12, 16, 18, "#5a3b26")  # door
    s.r(14, 14, 12, 16, "#6b4a2f")
    s.p(24, 22, "#d9a441")
    window(s, 40, 10, 18, 11, ("#cfe8f5", "#8ec5e8"))
    # fence
    for x in range(74, W - 4, 6):
        s.r(x, 16, 4, FLOOR - 16, "#eee8da")
        s.p(x, 16, mix("#6fb0e0", "#cfe8f5", 16 / FLOOR))
        s.p(x + 3, 16, mix("#6fb0e0", "#cfe8f5", 16 / FLOOR))
        s.vline(x + 3, 17, FLOOR - 17, "#cfc6b4")
    s.r(74, 20, W - 74, 1, "#cfc6b4")
    s.r(74, 26, W - 74, 1, "#cfc6b4")
    # big tree
    s.r(300, 10, 6, FLOOR - 10, "#6b4a2f")
    s.vline(302, 10, FLOOR - 10, "#7d5838")
    for dx, dy, rad, c in ((303, 6, 8, "#3f7a3a"), (292, 9, 6, "#4f8a45"), (314, 9, 6, "#4f8a45"), (298, 3, 5, "#5c9a50"), (309, 2, 5, "#5c9a50"), (303, 11, 5, "#3f7a3a")):
        s.disc(dx, dy, rad, c)
    for _ in range(14):
        s.p(rnd.randrange(290, 318), rnd.randrange(0, 14), "#b0413e")  # apples
    # bushes and flowers
    for bx in (120, 200, 380, 470, 590):
        s.disc(bx, FLOOR - 3, 4, "#3f7a3a")
        s.disc(bx + 6, FLOOR - 2, 3, "#4f8a45")
    for _ in range(70):
        x = rnd.randrange(74, W)
        c = rnd.choice(("#e07a7a", "#f2d48a", "#f3f7fa", "#c38ad4"))
        s.vline(x, FLOOR - 3, 2, "#3f7a3a")
        s.p(x, FLOOR - 4, c)
    # birdbath
    s.r(520, 20, 14, 2, "#b8bec4")
    s.r(522, 22, 10, 1, "#8ec5e8")
    s.vline(526, 22, 8, "#aeb4b9")
    s.r(523, FLOOR - 1, 8, 1, "#9aa1a8")
    s.r(525, 17, 3, 2, "#5a3a35")  # bird
    s.p(528, 17, "#d9a441")
    # lawn, path
    s.r(0, FLOOR, W, H - FLOOR, "#5c9a46")
    for _ in range(500):
        s.p(rnd.randrange(W), rnd.randrange(FLOOR, H), rnd.choice(("#4f8a3c", "#6aa852")))
    for x in range(4, 60, 9):
        s.r(x, FLOOR + 2 + (x % 2), 6, 3, "#b8b2a4")
    s.hline(0, FLOOR, W, "#4f8a3c")
    return s


def toits():
    rnd = random.Random(5)
    s = Pic("#141a33")
    for y in range(FLOOR):
        s.hline(0, y, W, mix("#10152b", "#2a3560", y / FLOOR))
    for _ in range(160):
        s.p(rnd.randrange(W), rnd.randrange(0, 18), rnd.choice(("#f4eecf", "#cfd8f5", "#8f9ac0")))
    s.disc(500, 7, 4, "#f3eccc")
    s.p(499, 6, "#d8d0aa")
    s.p(502, 8, "#d8d0aa")
    # buildings in the distance
    x = 0
    while x < W:
        bw = rnd.randrange(18, 40)
        top = rnd.randrange(8, 18)
        s.r(x, top, bw, FLOOR - top, "#222a45")
        for wy in range(top + 2, FLOOR - 2, 3):
            for wx in range(x + 2, x + bw - 2, 4):
                if rnd.random() < 0.28:
                    s.r(wx, wy, 2, 1, rnd.choice(("#f2c56b", "#f2d48a", "#e0956b")))
        x += bw + rnd.randrange(0, 6)
    # nearby roofs: chimneys, antenna, water tower
    for cx in (60, 190, 330, 450, 590):
        s.r(cx, 16, 8, FLOOR - 16, "#6b3d35")
        s.r(cx - 1, 15, 10, 2, "#7d4a40")
        for y in range(18, FLOOR, 3):
            s.hline(cx, y, 8, "#5a322b")
    s.vline(250, 6, 24, "#8f9ac0")
    s.hline(246, 9, 9, "#8f9ac0")
    s.hline(247, 12, 7, "#8f9ac0")
    s.r(384, 10, 18, 12, "#4a3a35")
    s.r(386, 7, 14, 3, "#5a463f")
    for x in (386, 397):
        s.vline(x, 22, 8, "#3a2d24")
    # zinc ledge then tiles: the cats' path
    s.r(0, FLOOR - 2, W, 2, "#7d8a9b")
    s.hline(0, FLOOR - 2, W, "#a5b1c0")
    for y in range(FLOOR, H, 3):
        s.hline(0, y, W, "#5a3a35")
        for x in range((y // 3) % 2 * 4, W, 8):
            s.r(x, y + 1, 7, 2, "#6e463f")
    return s


def grenier():
    rnd = random.Random(6)
    s = Pic("#6b4c33")
    for x in range(0, W, 7):  # vertical planks
        s.vline(x, 0, FLOOR, "#563c28")
        for y in range(rnd.randrange(2, 9), FLOOR, rnd.randrange(8, 14)):
            s.p(x + 3, y, "#5e432d")
    # sloping beams
    for base in range(0, W, 160):
        for i in range(16):
            s.r(base + i * 2, i, 3, 2, "#3e2a1c")
            s.r(base + 158 - i * 2, i, 3, 2, "#3e2a1c")
        s.r(base, 0, 160, 2, "#3e2a1c")
    # round window
    s.disc(300, 11, 7, "#3e2a1c")
    s.disc(300, 11, 6, "#9fb7d6")
    s.disc(298, 9, 2, "#dce6f2")
    s.vline(300, 5, 13, "#3e2a1c")
    s.hline(294, 11, 13, "#3e2a1c")
    # hanging bulb
    s.vline(150, 0, 9, "#2d2d33")
    s.r(148, 9, 5, 3, "#f2d48a")
    s.p(150, 12, "#f3eccc")
    # stacked boxes
    for bx, by, bw, bh in ((40, 18, 20, 12), (62, 21, 16, 9), (46, 9, 14, 9), (500, 16, 22, 14), (524, 22, 14, 8)):
        s.r(bx, by, bw, bh, "#b08a5a")
        s.hline(bx, by, bw, "#c29c6a")
        s.vline(bx + bw // 2, by, bh // 2, "#e2d2b0")
        s.frame(bx, by, bw, bh, "#8a6a42")
    # trunk
    s.r(190, 19, 30, 11, "#5a3a2a")
    s.r(190, 17, 30, 3, "#6b4632")
    for x in (194, 214):
        s.vline(x, 17, 13, "#c9a24a")
    s.r(203, 21, 4, 3, "#c9a24a")
    # rocking chair
    s.r(380, 8, 3, 18, "#3e2a1c")
    s.r(380, 19, 20, 3, "#3e2a1c")
    s.vline(397, 19, 9, "#3e2a1c")
    s.r(383, 10, 2, 9, "#8c3b3b")
    s.r(383, 17, 14, 2, "#8c3b3b")
    for i in range(24):
        s.p(376 + i, FLOOR - 1 + (1 if 4 < i < 20 else 0), "#3e2a1c")
    # piles of books, yarn balls, old mirror
    books(s, rnd, 240, 23, 12, 7)
    books(s, rnd, 254, 25, 8, 5)
    yarn(s, 268, FLOOR + 2, "#b0413e", "#8c2f2d")
    yarn(s, 446, FLOOR + 3, "#d9a441", "#b0842e")
    s.r(580, 6, 12, 22, "#c9a24a")
    s.r(582, 8, 8, 18, "#9fb7d6")
    s.p(584, 10, "#dce6f2")
    s.p(585, 11, "#dce6f2")
    # worn rug and floorboards
    planks(s, rnd, "#5a3f2b", "#46301f", "#68492f")
    s.r(400, FLOOR + 3, 80, 3, "#7a4f8c")
    for x in range(402, 478, 5):
        s.p(x, FLOOR + 4, "#a37ab5")
    return s


SCENES = {"salon": salon, "cuisine": cuisine, "bureau": bureau, "jardin": jardin, "toits": toits, "grenier": grenier}

if __name__ == "__main__":
    for name, draw in SCENES.items():
        draw().save(name)
        print(f"scenes/{name}.png")

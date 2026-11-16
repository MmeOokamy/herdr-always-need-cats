#!/usr/bin/env python3
"""Generates img/cat-<coat>-think.gif: the cat flips a crepe (when Claude is thinking).

    python3 make_think.py

The drawings (head, pan, crepe, coats) are copied from sprites.py of
we-always-need-cats, by MmeOokamy (MIT license, see ../LICENSE-cats), so as not to
depend on the original repository or on PyQt6. The rendering (halo, scale, GIF) is that of
make_sprites.py. Requires Pillow.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_sprites import OUT, SYMBOLS_H, U, Canvas, save  # noqa: E402

CELL_W, CELL_H = 22, 18
FPS = 5

_HEAD_TOP = [
    "..KK........KK....",
    ".KFFK......KFFK...",
    ".KFPFKKKKKKFPFK...",
    ".KFFFSFSSFSFFFK...",
    ".KFFFFFSSFFFFFK...",
]
_EYES = {
    "open": [".KFEEFFFFFFEEFK...", ".KFEEFFPPFFEEFK..."],
    "lowered": [".KFFFFFFFFFFFFK...", ".KFEEFFPPFFEEFK..."],
}
_MOUTH = {
    "closed": [".KFFFWWWWWWFFFK...", "..KFFFWWWWFFFK....", "...KKKKKKKKKK....."],
    "open": [".KFFFWWWWWWFFFK...", "..KFFFWPPWFFFK....", "...KKKKKKKKKK....."],
}


def head(eyes, mouth="closed"):
    return [line + ".." for line in _HEAD_TOP + _EYES[eyes] + _MOUTH[mouth]]


PAN_FULL = [
    "..KFFFFFFFFFFK......",
    ".KFKCCBCCCBCKFFK....",
    "KGGGGGGGGGGGGGGKKKKK",
    ".KGGGGGGGGGGGGKFFFK.",
    ".KFFKFFKKFFKFFFFK...",
    ".KKKKKKKKKKKKKKK....",
]
PAN_EMPTY = [
    "..KFFFFFFFFFFK......",
    ".KFFFWWWWWWFFFK.....",
    "KGGGGGGGGGGGGGGKKKKK",
    ".KGGGGGGGGGGGGKFFFK.",
    ".KFFKFFKKFFKFFFFK...",
    ".KKKKKKKKKKKKKKK....",
]
PAN_UP = [
    "..KFFFFFFFFFFK......",
    "KGGGGGGGGGGGGGGKKKKK",
    ".KGGGGGGGGGGGGKFFFK.",
    ".KFFKFWWWWFKFFK.....",
    ".KFFKFFKKFFKFFFFK...",
    ".KKKKKKKKKKKKKKK....",
]
IMAGES = {
    "flip_full": head("lowered") + PAN_FULL,
    "flip_empty": head("open", "open") + PAN_EMPTY,
    "flip_up": head("open", "open") + PAN_UP,
    "crepe_flat": [".KKKKKK.", "KCCBCCBK", ".KKKKKK."],
    "crepe_flipped": [".KKKKKK.", "KBCBBCBK", ".KKKKKK."],
    "crepe_tilted": ["...KK", "..KCK", ".KBK.", "KCK..", "KK..."],
}
THINK = ["flip_full", "flip_full", "flip_up", "flip_empty", "flip_empty", "flip_empty", "flip_up", "flip_full"]
# The crepe, frame by frame: (drawing, column, line, flipped) in cat pixels, or None (in the pan).
FLIGHT = [
    None,
    None,
    ("crepe_flat", 4, -1, False),
    ("crepe_tilted", 6, -4, False),
    ("crepe_flipped", 4, -6, False),
    ("crepe_tilted", 6, -4, True),
    ("crepe_flat", 4, -1, False),
    None,
]
COATS = [
    {"name": "ginger", "F": "#F0A04B", "S": "#C9742A", "W": "#FFF4E3"},
    {"name": "grey", "F": "#9AA5B4", "S": "#6F7A8A", "W": "#F4F6F8"},
    {"name": "black", "F": "#55516A", "S": "#3C3950", "W": "#E9E6F2"},
    {"name": "cream", "F": "#F3E3C3", "S": "#D9BE8E", "W": "#FFFFFF"},
    {"name": "brown", "F": "#A9764F", "S": "#7E5334", "W": "#F7EADB"},
    {"name": "blue", "F": "#7FA8C9", "S": "#5A84A6", "W": "#F0F7FC"},
]


def palette(coat):
    return {"K": "#2B2230", "F": coat["F"], "S": coat["S"], "W": coat["W"], "P": "#F58CA8",
            "E": "#2B2230", "G": "#5B6472", "C": "#F6C86E", "B": "#C98A3A"}


def frames(coat):
    colors = palette(coat)
    out = []
    for index, name in enumerate(THINK):
        canvas = Canvas(CELL_W, SYMBOLS_H + CELL_H)
        lines = IMAGES[name]
        width, height = max(len(line) for line in lines) + 2, len(lines) + 2
        x = (CELL_W - width) // 2 * U + U
        y = canvas.h - height * U + U
        canvas.sprite(lines, colors, x, y)
        flight = FLIGHT[index]
        if flight:
            crepe, column, line, flipped = flight
            drawing = IMAGES[crepe]
            if flipped:
                drawing = [row[::-1] for row in drawing]
            canvas.sprite(drawing, colors, x + column * U, y + line * U)
        out.append(canvas)
    return out


if __name__ == "__main__":
    for coat in COATS:
        save(f"{OUT}/cat-{coat['name']}-think.gif", frames(coat), FPS)
    print(f"{len(COATS)} GIF écrits dans {OUT}")

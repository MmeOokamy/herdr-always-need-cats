#!/usr/bin/env python3
"""Generates the animated images (WebP) of the usage cat for the Herdr mod.

The drawings are in tools/drawings.py:

- usage cat (usage-cat/sprites): as usage_cat.py paints it (cat,
  symbols above it, jump of joy), one image per coat, animation and level;
- agent cats (agents-cats/sprites): the cat alone, without symbols, one
  image per coat (cats and kittens) and animation.

Usage: python3 tools/make_sprites.py
"""

import math
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "usage-cat", "sprites")
OUT_AGENTS = os.path.join(ROOT, "agents-cats", "sprites")
# Agent cat animations (Herdr state -> animation: see agents-cats).
AGENT_ANIMATIONS = ("idle", "work", "question", "done", "sleep")
AGENT_SCREEN = "read"  # color of the computer screen (blue)

sys.path.insert(0, HERE)
import drawings as sprites  # noqa: E402  (drawings and colors)

# Usage levels, from calmest to worst, and their color (gauges, screen).
LEVELS = ("none", "ok", "warn", "alert", "critical", "full")
LEVEL_COLOR = {
    "none": "#868E96",
    "ok": "#2F9E44",
    "warn": "#F2B01E",
    "alert": "#E8590C",
    "critical": "#E03131",
    "full": "#E03131",
}

# Working grid: 1 drawing pixel = 2 units (the small symbols are
# half-size), 1 unit = UNIT pixels in the output image.
UNIT = 4
SYMBOLS_H = 7  # space above the cat, in drawing pixels
W = sprites.CELL_W
H = SYMBOLS_H + sprites.CELL_H
STAR = "#FFD43B"
ZZZ = "#FFFFFF"

FPS = {"idle": 3, "question": 3, "panic": 6, "done": 4, "work": 5, "sleep": 1.5}
FRAMES = dict(sprites.ANIMATIONS, panic=sprites.ANIMATIONS["question"])
# Period of the symbols, so that the animation loops without a jump.
SYMBOL_PERIOD = {"work": 6, "done": 3, "sleep": 2, "question": 2, "panic": 2, "idle": 1}

# A working cat switches in turn, like the office cats that think,
# from its computer to the crepes, the yarn ball and the Rubik's cube
# (TURN frames each, at 5 frames per second). The "work" images hold
# the whole cycle.
TURNS = ("work", "think", "play", "cube")
TURN = 16  # frames per turn
OVERLAYS = {"play": sprites.YARN_PLAY, "cube": sprites.CUBE_SOLVE}


def overlays(animation, index):
    """What is drawn over the cat: crepe in the air, yarn ball, cube."""
    if animation == "think":
        flight = sprites.CREPE_FLIGHT[index % len(sprites.CREPE_FLIGHT)]
        return [flight] if flight else []
    frames = OVERLAYS.get(animation)
    return frames[index % len(frames)] if frames else []


def working(index, start=0):
    """(turn animation, drawing name, objects drawn over it) of frame index
    of the work cycle; start shifts the first turn."""
    turn = TURNS[(index // TURN + start) % len(TURNS)]
    i = index % TURN
    names = sprites.ANIMATIONS[turn]
    return turn, names[i % len(names)], overlays(turn, i)


def rgba(color):
    color = color.lstrip("#")
    if len(color) == 8:  # #AARRGGBB (Qt format)
        a, r, g, b = (int(color[i : i + 2], 16) for i in range(0, 8, 2))
        return (r, g, b, a)
    return tuple(int(color[i : i + 2], 16) for i in range(0, 6, 2)) + (255,)


class Canvas:
    """Image in units of 1/2 drawing pixel."""

    def __init__(self, w=W, h=H):
        self.w, self.h = w * 2, h * 2
        self.pixels = {}

    def put(self, x, y, color, size=2):
        for dx in range(size):
            for dy in range(size):
                if 0 <= x + dx < self.w and 0 <= y + dy < self.h:
                    self.pixels[(x + dx, y + dy)] = color

    def sprite(self, lines, colors, left, top):
        """Drawing with its light halo, in drawing pixels (like sprites.draw)."""
        filled = set()
        for j, line in enumerate(lines):
            for i, char in enumerate(line):
                if char in colors:
                    filled.add((left + i, top + j))
        halo = rgba(sprites.HALO)
        for x, y in filled:
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if (nx, ny) not in filled:
                    self.put(nx * 2, ny * 2, halo)
        for j, line in enumerate(lines):
            for i, char in enumerate(line):
                if char in colors:
                    self.put((left + i) * 2, (top + j) * 2, rgba(colors[char]))

    def symbol(self, name, x, y, color, size):
        """Symbol in units; size = 2 (full size) or 1 (half)."""
        for j, line in enumerate(sprites.SYMBOLS[name]):
            for i, char in enumerate(line):
                if char == "K":
                    self.put(x + i * size, y + j * size, rgba(color), size)

    def image(self):
        image = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        for (x, y), color in self.pixels.items():
            image.putpixel((x, y), color)
        return image.resize((self.w * UNIT, self.h * UNIT), Image.NEAREST)


def frame(coat, level, animation, index):
    """One image, like UsageCat.paint (without gauges or bubble: the mod draws them)."""
    even = index % 2 == 0
    color = LEVEL_COLOR[level]
    items = []
    if animation == "work":
        turn, name, items = working(index)
    else:
        turn, names = animation, FRAMES[animation]
        name = names[index % len(names)]
    lines = sprites.IMAGES[name]
    colors = sprites.palette(coat, level)
    canvas = Canvas()
    sprite_w, sprite_h = len(lines[0]) + 2, len(lines) + 2
    jump = 2 if (animation == "done" and even) else 0
    left = (sprites.CELL_W - sprite_w) // 2 + 1
    top = H - sprite_h - jump + 1
    canvas.sprite(lines, colors, left, top)
    for item, column, line, _mirror in items:
        canvas.sprite(sprites.IMAGES[item], colors, left + column, top + line)
    cat_top = SYMBOLS_H * 2  # in units
    if animation == "sleep":
        canvas.symbol("z", (W - 5) * 2, cat_top + (3 if even else 2) * 2, ZZZ, 1)
        if even:
            canvas.symbol("z", (W - 2) * 2 - 4, cat_top - 2, ZZZ, 1)
    elif animation in ("question", "panic"):
        canvas.symbol("!", (W - 3) * 2, cat_top - (6 if even else 5) * 2, color, 2)
    elif animation == "done":
        for i, (sx, sy) in enumerate(((1, -4), (15, -6), (9, -7))):
            if (index + i) % 3:
                canvas.symbol("star", sx * 2, cat_top + sy * 2 + jump, STAR, 2)
    elif animation == "work" and turn == "work":  # in front of the computer
        for i in range(3):
            phase = (index + i * 2) % 6
            if phase < 5:
                canvas.symbol("!", (6 + i * 3) * 2, cat_top - phase * 2, color, 1)
    return canvas.image()


def agent_frame(coat, animation, index, start=0):
    """The cat alone, in a cell the size of the drawing (+2 lines for the jump)."""
    items = []
    if animation == "work":
        _turn, name, items = working(index, start)
    else:
        names = FRAMES[animation]
        name = names[index % len(names)]
    lines = sprites.IMAGES[name]
    colors = sprites.palette(coat, AGENT_SCREEN)
    h = sprites.CELL_H + 2
    canvas = Canvas(sprites.CELL_W, h)
    sprite_w, sprite_h = len(lines[0]) + 2, len(lines) + 2
    jump = 2 if (animation == "done" and index % 2 == 0) else 0
    left = (sprites.CELL_W - sprite_w) // 2 + 1
    top = h - sprite_h - jump + 1
    canvas.sprite(lines, colors, left, top)
    for item, column, line, _mirror in items:
        # Little room above the head: the crepe does not fly as high.
        line = max(line, 1 - top)
        canvas.sprite(sprites.IMAGES[item], colors, left + column, top + line)
    return canvas.image()


def save(images, path, fps):
    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        duration=round(1000 / fps),
        loop=0,
        lossless=True,
    )


def make_agents():
    os.makedirs(OUT_AGENTS, exist_ok=True)
    count = 0
    # Each coat starts its work cycle at a different turn: two neighboring
    # agents do not do the same thing at the same time.
    coats = list(enumerate(sprites.COATS)) + list(enumerate(sprites.KITTEN_COATS))
    for number, coat in coats:
        for animation in AGENT_ANIMATIONS:
            length = len(FRAMES[animation]) if animation != "done" else 2
            if animation == "work":
                length = TURN * len(TURNS)
            images = [agent_frame(coat, animation, i, number) for i in range(length)]
            save(images, os.path.join(OUT_AGENTS, f"{coat['name']}-{animation}.webp"), FPS[animation])
            count += 1
    print(f"{count} images dans {OUT_AGENTS}")


def main():
    sprites.SCREENS.update(LEVEL_COLOR)  # the screen takes the color of the level
    os.makedirs(OUT, exist_ok=True)
    count = 0
    for coat in sprites.COATS:
        for animation, names in FRAMES.items():
            if animation not in FPS:
                continue
            length = len(names) * SYMBOL_PERIOD[animation] // math.gcd(len(names), SYMBOL_PERIOD[animation])
            if animation == "work":
                length = TURN * len(TURNS)  # the whole cycle
            duration = round(1000 / FPS[animation])
            for level in LEVELS:
                images = [frame(coat, level, animation, i) for i in range(length)]
                path = os.path.join(OUT, f"{coat['name']}-{animation}-{level}.webp")
                images[0].save(
                    path,
                    save_all=True,
                    append_images=images[1:],
                    duration=duration,
                    loop=0,
                    lossless=True,
                )
                count += 1
    print(f"{count} images dans {OUT}")
    make_agents()


if __name__ == "__main__":
    main()

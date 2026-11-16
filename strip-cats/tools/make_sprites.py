#!/usr/bin/env python3
"""Generates the mod's animated GIFs from the drawings of we-always-need-cats.

    python3 make_sprites.py /path/to/we-always-need-cats

The GIFs are already provided in img/: this script is only needed after the
drawings are touched up. It requires Pillow, and PyQt6 (imported by the project's sprites.py).
"""

import os
import sys

from PIL import Image

U = 2  # internal units per drawing pixel (the symbols are at half scale)
ZOOM = 3  # final enlargement: 6 image px per drawing pixel
SYMBOLS_H = 7  # drawing pixels reserved above the cat
HALO = (244, 244, 244)
FPS = {"idle": 3, "question": 3, "done": 4, "work": 4, "sleep": 1.5, "run": 9, "meow": 3}
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img")


def rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


class Canvas:
    """Pixel grid in internal units; None = transparent."""

    def __init__(self, width, height):
        self.w, self.h = width * U, height * U
        self.px = {}

    def rect(self, x, y, size, color):
        for j in range(size):
            for i in range(size):
                if 0 <= x + i < self.w and 0 <= y + j < self.h:
                    self.px[(x + i, y + j)] = color

    def sprite(self, lines, colors, x, y):
        """Full-scale drawing with its light halo, top-left corner at (x, y)."""
        filled = set()
        for j, line in enumerate(lines):
            for i, char in enumerate(line):
                if char in colors:
                    filled.add((i, j))
                    self.rect(x + i * U, y + j * U, U, rgb(colors[char]))
        for i, j in filled:
            for ni, nj in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                if (ni, nj) not in filled:
                    self.rect(x + ni * U, y + nj * U, U, HALO)

    def symbol(self, lines, x, y, color, size):
        for j, line in enumerate(lines):
            for i, char in enumerate(line):
                if char == "K":
                    self.rect(x + i * size, y + j * size, size, rgb(color))


def save(path, canvases, fps):
    palette = [(255, 0, 255)]
    frames = []
    for canvas in canvases:
        image = Image.new("P", (canvas.w, canvas.h), 0)
        for (x, y), color in canvas.px.items():
            if color not in palette:
                palette.append(color)
            image.putpixel((x, y), palette.index(color))
        frames.append(image)
    flat = [channel for color in palette for channel in color]
    flat += [0] * (768 - len(flat))
    out = []
    for image in frames:
        image.putpalette(flat)
        out.append(image.resize((image.width * ZOOM, image.height * ZOOM), Image.NEAREST))
    out[0].save(
        path,
        save_all=True,
        append_images=out[1:],
        duration=round(1000 / fps),
        loop=0,
        disposal=2,
        transparency=0,
        background=0,
    )


def mirrored(canvas):
    flipped = Canvas(0, 0)
    flipped.w, flipped.h = canvas.w, canvas.h
    flipped.px = {(canvas.w - 1 - x, y): color for (x, y), color in canvas.px.items()}
    return flipped


def cat_frames(sprites, animation, coat, activity):
    # "meow": the "question" meow, without the question mark (usage cat).
    names = sprites.ANIMATIONS["question" if animation == "meow" else animation]
    count = {"idle": len(names), "question": 2, "meow": 2, "run": 2, "done": 6, "work": 6, "sleep": 6}[animation]
    colors = sprites.palette(coat, activity)
    cell_w, cell_h = sprites.CELL_W, sprites.CELL_H
    top = SYMBOLS_H * U  # top of the cat's cell
    frames = []
    for index in range(count):
        even = index % 2 == 0
        canvas = Canvas(cell_w, SYMBOLS_H + cell_h)
        lines = sprites.IMAGES[names[index % len(names)]]
        width, height = max(len(line) for line in lines) + 2, len(lines) + 2
        jump = 2 * U if (animation == "done" and even) else 0
        x = (cell_w - width) // 2 * U + U
        y = canvas.h - height * U - jump + U
        canvas.sprite(lines, colors, x, y)
        if animation == "sleep":
            canvas.symbol(sprites.SYMBOLS["z"], (cell_w - 5) * U, top + (3 if even else 2) * U, "#B9C8DC", 1)
            if even:
                canvas.symbol(sprites.SYMBOLS["z"], (cell_w - 2) * U - 2, top - U, "#B9C8DC", 1)
        elif animation == "question":
            canvas.symbol(sprites.SYMBOLS["?"], (cell_w - 4) * U, top - (6 if even else 5) * U, "#E8590C", U)
        elif animation == "done":
            for i, (sx, sy) in enumerate(((1, -4), (15, -6), (9, -7))):
                if (index + i) % 3:
                    canvas.symbol(sprites.SYMBOLS["star"], sx * U, top + sy * U + jump // 2, "#FFD43B", U)
        elif animation == "work":
            screen = sprites.SCREENS.get(activity, sprites.SCREENS["think"])
            for i in range(3):
                phase = (index + i * 2) % 6
                if phase < 5:
                    canvas.symbol(sprites.SYMBOLS["!"], (6 + i * 3) * U, top - phase * U, screen, 1)
        frames.append(canvas)
    return frames


def kitten_frames(sprites, coat, activity):
    colors = sprites.palette(coat, activity)
    frames = []
    for name in sprites.ANIMATIONS["work"]:
        lines = sprites.IMAGES[name]
        canvas = Canvas(sprites.CELL_W, sprites.CELL_H)
        width, height = max(len(line) for line in lines) + 2, len(lines) + 2
        canvas.sprite(lines, colors, (sprites.CELL_W - width) // 2 * U + U, canvas.h - height * U + U)
        frames.append(canvas)
    return frames


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.path.insert(0, sys.argv[1])
    import sprites

    os.makedirs(OUT, exist_ok=True)
    count = 0
    for coat in sprites.COATS:
        for animation in ("idle", "question", "done", "sleep", "meow"):
            save(f"{OUT}/cat-{coat['name']}-{animation}.gif", cat_frames(sprites, animation, coat, "think"), FPS[animation])
            count += 1
        run = cat_frames(sprites, "run", coat, "think")
        save(f"{OUT}/cat-{coat['name']}-run-r.gif", run, FPS["run"])
        save(f"{OUT}/cat-{coat['name']}-run-l.gif", [mirrored(c) for c in run], FPS["run"])
        count += 2
        for activity in sprites.SCREENS:
            save(f"{OUT}/cat-{coat['name']}-work-{activity}.gif", cat_frames(sprites, "work", coat, activity), FPS["work"])
            count += 1
    for coat in sprites.KITTEN_COATS:
        for activity in sprites.SCREENS:
            save(f"{OUT}/kit-{coat['name']}-{activity}.gif", kitten_frames(sprites, coat, activity), FPS["work"])
            count += 1
    print(f"{count} GIF écrits dans {OUT}")


if __name__ == "__main__":
    main()

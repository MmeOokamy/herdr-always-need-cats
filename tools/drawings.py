"""Dessins pixel art des chats (copie de sprites.py de we-always-need-cats, sans Qt).

Every sprite is a list of text lines, one character per pixel:

    .  transparent        K  outline
    F  fur                S  stripes (darker fur)
    W  white (muzzle, belly)
    P  pink (ears, nose, mouth)
    E  eyes
    G  laptop shell, frying pan
    L  laptop screen (color depends on the activity)
    C  crepe              B  browned spots of the crepe

Après une modification : python3 tools/make_sprites.py
"""

# Size of the cell each sprite is placed in (bottom-aligned, centered).
# It includes one pixel of margin on every side for the light halo.
CELL_W = 22
CELL_H = 18

# --- Front head (10 lines), with variants for the eyes and the mouth --------

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
    "happy": [".KFFEFFFFFFEFFK...", ".KFEFEFPPFEFEFK..."],
}
_MOUTH = {
    "closed": [".KFFFWWWWWWFFFK...", "..KFFFWWWWFFFK....", "...KKKKKKKKKK....."],
    "open": [".KFFFWWWWWWFFFK...", "..KFFFWPPWFFFK....", "...KKKKKKKKKK....."],
}


def _head(eyes, mouth="closed"):
    return _HEAD_TOP + _EYES[eyes] + _MOUTH[mouth]


# --- Front body (6 lines) ---------------------------------------------------

_BODY_TAIL_DOWN = [
    "..KFFFFFFFFFFK....",
    ".KFFFWWWWWWFFFK...",
    ".KFFFWWWWWWFFFK.KK",
    ".KFFKFWWWWFKFFKKFK",
    ".KFFKFFKKFFKFFFFK.",
    ".KKKKKKKKKKKKKKK..",
]
_BODY_TAIL_UP = [
    "..KFFFFFFFFFFK..KK",
    ".KFFFWWWWWWFFFK.KF",
    ".KFFFWWWWWWFFFK.KF",
    ".KFFKFWWWWFKFFKKFK",
    ".KFFKFFKKFFKFFFFK.",
    ".KKKKKKKKKKKKKKK..",
]
_BODY_ARMS_UP = [
    "KFKFFFFFFFFFFKFK..",
    "KFFFFWWWWWWFFFFK..",
    ".KKFFWWWWWWFFKK...",
    "..KFKFWWWWFKFK....",
    "..KFKFFKKFFKFK....",
    "..KKKKKKKKKKKK....",
]
_BODY_LAPTOP_LEFT = [
    "..KFFFFFFFFFFK....",
    ".KGGGGGGGGGGGGK...",
    "KFGLLLLLLLLLLGK...",
    "KKGLLLLWWLLLLGKFK.",
    ".KGLLLLLLLLLLGKKK.",
    "KKKKKKKKKKKKKKKK..",
]
_BODY_LAPTOP_RIGHT = [
    "..KFFFFFFFFFFK....",
    ".KGGGGGGGGGGGGK...",
    ".KGLLLLLLLLLLGKFK.",
    "KFGLLLLWWLLLLGKKK.",
    "KKGLLLLLLLLLLGK...",
    "KKKKKKKKKKKKKKKK..",
]

# --- Crepe flipping (thinking): 20 pixels wide, the pan handle sticks out ---

_BODY_PAN_FULL = [  # pan held low, the crepe in it
    "..KFFFFFFFFFFK......",
    ".KFKCCBCCCBCKFFK....",
    "KGGGGGGGGGGGGGGKKKKK",
    ".KGGGGGGGGGGGGKFFFK.",
    ".KFFKFFKKFFKFFFFK...",
    ".KKKKKKKKKKKKKKK....",
]
_BODY_PAN_EMPTY = [  # pan held low, the crepe is in the air
    "..KFFFFFFFFFFK......",
    ".KFFFWWWWWWFFFK.....",
    "KGGGGGGGGGGGGGGKKKKK",
    ".KGGGGGGGGGGGGKFFFK.",
    ".KFFKFFKKFFKFFFFK...",
    ".KKKKKKKKKKKKKKK....",
]
_BODY_PAN_UP = [  # pan raised: throwing or catching the crepe
    "..KFFFFFFFFFFK......",
    "KGGGGGGGGGGGGGGKKKKK",
    ".KGGGGGGGGGGGGKFFFK.",
    ".KFFKFWWWWFKFFK.....",
    ".KFFKFFKKFFKFFFFK...",
    ".KKKKKKKKKKKKKKK....",
]


def _wide(lines):
    """Head lines widened to the 20 pixels of the pan bodies."""
    return [line + ".." for line in lines]


# The flying crepe, drawn on its own above the cat by cats.py.
_CREPE_FLAT = [".KKKKKK.", "KCCBCCBK", ".KKKKKK."]
_CREPE_FLIPPED = [".KKKKKK.", "KBCBBCBK", ".KKKKKK."]
_CREPE_TILTED = ["...KK", "..KCK", ".KBK.", "KCK..", "KK..."]

# --- Side views -------------------------------------------------------------

_RUN_A = [
    "K.............K.K...",
    "KK...........KFKFK..",
    ".KK.KKKKKKKKKKFFFFK.",
    "..KKFFSFSFSFFFFEFFPK",
    "..KFFFFFFFFFFFFFFWWK",
    "..KFFFFFFFFFFFFFKKK.",
    "..KFFFFFFFFFFFWK....",
    ".KFFKKKKKKKKFFK.....",
    "KFFK........KFFK....",
    "KKK..........KKK....",
]
_RUN_B = [
    "..............K.K...",
    ".K...........KFKFK..",
    "KFK.KKKKKKKKKKFFFFK.",
    "KFKKFFSFSFSFFFFEFFPK",
    ".KFFFFFFFFFFFFFFFWWK",
    "..KFFFFFFFFFFFFFKKK.",
    "..KFFFFFFFFFFFWK....",
    "..KKFFKKKKKFFKK.....",
    "...KFFK...KFFK......",
    "....KK.....KK.......",
]
_SLEEP_A = [
    "..K..K..KKKKKKK.....",
    ".KFKKFKKFFSFSFFKK...",
    ".KFFFFFFFFFFFFFFFK..",
    "KFFFFFFFFFFFFFFFFFK.",
    "KFEEFFEEFFFFFFFFFFK.",
    "KFFFPPFFFFFFFKKKKFK.",
    ".KWWWWWFFFFFKFFFFK..",
    "..KKKKKKKKKKKKKKK...",
]
_SLEEP_B = [
    "....................",
    "..K..K..KKKKKKK.....",
    ".KFKKFKKFFSFSFFKK...",
    "KFFFFFFFFFFFFFFFFFK.",
    "KFEEFFEEFFFFFFFFFFK.",
    "KFFFPPFFFFFFFKKKKFK.",
    ".KWWWWWFFFFFKFFFFK..",
    "..KKKKKKKKKKKKKKK...",
]

IMAGES = {
    "sit_a": _head("open") + _BODY_TAIL_DOWN,
    "sit_b": _head("open") + _BODY_TAIL_UP,
    "sit_blink": _head("lowered") + _BODY_TAIL_DOWN,
    "meow_a": _head("open", "open") + _BODY_TAIL_UP,
    "meow_b": _head("open") + _BODY_TAIL_DOWN,
    "happy_a": _head("happy", "open") + _BODY_ARMS_UP,
    "happy_b": _head("happy") + _BODY_TAIL_UP,
    "work_a": _head("lowered") + _BODY_LAPTOP_LEFT,
    "work_b": _head("lowered") + _BODY_LAPTOP_RIGHT,
    "flip_full": _wide(_head("lowered")) + _BODY_PAN_FULL,
    "flip_empty": _wide(_head("open", "open")) + _BODY_PAN_EMPTY,
    "flip_up": _wide(_head("open", "open")) + _BODY_PAN_UP,
    "crepe_flat": _CREPE_FLAT,
    "crepe_flipped": _CREPE_FLIPPED,
    "crepe_tilted": _CREPE_TILTED,
    "run_a": _RUN_A,
    "run_b": _RUN_B,
    "sleep_a": _SLEEP_A,
    "sleep_b": _SLEEP_B,
}

# Animations: sequences of sprites played in a loop.
ANIMATIONS = {
    "idle": ["sit_a"] * 4 + ["sit_b"] * 4 + ["sit_a"] * 3 + ["sit_blink"],
    "question": ["meow_a", "meow_b"],
    "done": ["happy_a", "happy_b"],
    "work": ["work_a", "work_b"],
    # Thinking: the cat flips a crepe (see CREPE_FLIGHT for the crepe itself).
    "think": [
        "flip_full",
        "flip_full",
        "flip_up",
        "flip_empty",
        "flip_empty",
        "flip_empty",
        "flip_up",
        "flip_full",
    ],
    "run": ["run_a", "run_b"],
    "sleep": ["sleep_a"] * 3 + ["sleep_b"] * 3,
}

# Flying crepe, frame by frame of the "think" animation: (sprite, column, line,
# mirrored), in pixels of the cat sprite (line < 0: above the cat), or None
# while the crepe lies in the pan.
CREPE_FLIGHT = [
    None,
    None,
    ("crepe_flat", 4, -1, False),  # thrown, already above the head
    ("crepe_tilted", 6, -4, False),  # turning over
    ("crepe_flipped", 4, -6, False),  # top of the flight (stays under the bubble)
    ("crepe_tilted", 6, -4, True),  # falling back
    ("crepe_flat", 4, -1, False),  # about to land in the pan
    None,
]

# Small symbols drawn above the cat.
SYMBOLS = {
    "?": ["KKK.", "..K.", ".KK.", ".K..", "....", ".K.."],
    "!": ["K", "K", "K", "K", ".", "K"],
    "z": ["KKKK", "..K.", ".K..", "KKKK"],
    "star": [".K.", "KKK", ".K."],
}

# --- Colors -----------------------------------------------------------------

OUTLINE = "#2B2230"
# Light halo around the drawing, to stay readable on a dark background.
HALO = "#D9FFFFFF"

# Cat coats (one per Claude Code session).
COATS = [
    {"name": "ginger", "F": "#F0A04B", "S": "#C9742A", "W": "#FFF4E3"},
    {"name": "grey", "F": "#9AA5B4", "S": "#6F7A8A", "W": "#F4F6F8"},
    {"name": "black", "F": "#55516A", "S": "#3C3950", "W": "#E9E6F2"},
    {"name": "cream", "F": "#F3E3C3", "S": "#D9BE8E", "W": "#FFFFFF"},
    {"name": "brown", "F": "#A9764F", "S": "#7E5334", "W": "#F7EADB"},
    {"name": "blue", "F": "#7FA8C9", "S": "#5A84A6", "W": "#F0F7FC"},
]

# Kitten coats (one per subagent type).
KITTEN_COATS = [
    {"name": "pink", "F": "#F7A8C4", "S": "#DB7FA2", "W": "#FFF2F7"},
    {"name": "mint", "F": "#8FD9B6", "S": "#62B891", "W": "#F1FFF8"},
    {"name": "lavender", "F": "#B9A6F0", "S": "#917BD1", "W": "#F6F2FF"},
    {"name": "sky", "F": "#8CCBF2", "S": "#5FA6D1", "W": "#F0F9FF"},
    {"name": "lemon", "F": "#F2DC7A", "S": "#D1B74C", "W": "#FFFCE8"},
    {"name": "coral", "F": "#F59A85", "S": "#D4735D", "W": "#FFF1EE"},
]

# Laptop screen color, depending on the activity.
SCREENS = {
    "think": "#DDE3EA",
    "write": "#7CE38B",
    "read": "#7CC4FF",
    "shell": "#FFC857",
    "web": "#C59BFF",
    "agent": "#FF9ECF",
}


def palette(coat, activity="think"):
    """Character -> color table for a coat and an activity."""
    return {
        "K": OUTLINE,
        "F": coat["F"],
        "S": coat["S"],
        "W": coat["W"],
        "P": "#F58CA8",
        "E": "#2B2230",
        "G": "#5B6472",
        "L": SCREENS.get(activity, SCREENS["think"]),
        "C": "#F6C86E",
        "B": "#C98A3A",
    }

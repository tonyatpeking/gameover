from enum import Enum
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button
from gameover.input.windows_constants import *


large = r"""
+-----------------------------------------+     +-----------------------------------------+
| Esc |  1  |  2  |  3  |  4  |  5  |  `  |     |  =  |  6  |  7  |  8  |  9  |  0  |  -  |
|-----+-----+-----+-----+-----+-----+-----|     |-----+-----+-----+-----+-----+-----+-----|
| Tab |  Q  |  W  |  E  |  R  |  T  |  ^  |     |  ^  |  Y  |  U  |  I  |  O  |  P  |  \  |
|-----+-----+-----+-----+-----+-----|     |     |     |-----+-----+-----+-----+-----+-----|
| CAS |  A  |  S  |  D  |  F  |  G  |  (  |     |  )  |  H  |  J  |  K  |  L  |  ;  |  '  |
|-----+-----+-----+-----+-----+-----|-----|     |-----|-----+-----+-----+-----+-----+-----|
| LSf |  Z  |  X  |  C  |  V  |  B  |  [  |     |  ]  |  N  |  M  |  ,  |  .  |  /  | RSf |
+-----+-----+-----+-----+-----+-----+-----+     +-----+-----+-----+-----+-----+-----+-----+
| Ctl | C+A | Alt | Lft | Rgt |                             |  Up | Dwn |  L1 |  L2 | Win |
+-----------------------------+-----------+     +-----------+-----------------------------+
                              |  F2 | F11 |     | Hom | End |
                        +-----|-----|-----|     |-----+-----+-----+
                        |  ^  |  ^  | F12 |     | PgU |  ^  |  ^  |
                        |     |     |-----|     |-----|     |     |
                        | BkS | Del |  F5 |     | PgD | Ent | Spc |
                        +-----------------+     +-----------------+
"""




keystr_to_vk = {
    'LButton': VK_LBUTTON,
    'RButton': VK_RBUTTON,
    'MButton': VK_MBUTTON,
    'XButton1': VK_XBUTTON1,
    'XButton2': VK_XBUTTON2,
    'BkS': VK_BACK,
    'Tab': VK_TAB,
    'Ent': VK_RETURN,
    'LSf': VK_LSHIFT,
    'RSf': VK_RSHIFT,
    'Ctl': VK_LCONTROL,
    'Alt': VK_LMENU,
    'C+A': ('and', VK_LCONTROL, VK_LMENU),
    'CAS': ('and', VK_LCONTROL, VK_LMENU, VK_LSHIFT),
    'Esc': VK_ESCAPE,
    'Spc': VK_SPACE,
    'PgU': VK_PRIOR,
    'PgD': VK_NEXT,
    'End': VK_END,
    'Hom': VK_HOME,
    'Lft': VK_LEFT,
    'Up': VK_UP,
    'Rgt': VK_RIGHT,
    'Dwn': VK_DOWN,
    'Del': VK_DELETE,
    'Win': VK_LWIN,
    
    'F2': VK_F2,
    'F11': VK_F11,
    'F12': VK_F12,
    'F5': VK_F5,

    '`': VK_OEM_3,
    '=': VK_OEM_PLUS,
    '-': VK_OEM_MINUS,
    '\\': VK_OEM_5,
    '(': ('and',VK_LSHIFT, VK_9),
    ')': ('and',VK_LSHIFT, VK_0),
    ';': VK_OEM_1,
    "'": VK_OEM_7,
    '[': VK_OEM_4,
    ']': VK_OEM_6,
    ',': VK_OEM_COMMA,
    '.': VK_OEM_PERIOD,
    '/': VK_OEM_2,

    '0': VK_0,
    '1': VK_1,
    '2': VK_2,
    '3': VK_3,
    '4': VK_4,
    '5': VK_5,
    '6': VK_6,
    '7': VK_7,
    '8': VK_8,
    '9': VK_9,

    'A': VK_A,
    'B': VK_B,
    'C': VK_C,
    'D': VK_D,
    'E': VK_E,
    'F': VK_F,
    'G': VK_G,
    'H': VK_H,
    'I': VK_I,
    'J': VK_J,
    'K': VK_K,
    'L': VK_L,
    'M': VK_M,
    'N': VK_N,
    'O': VK_O,
    'P': VK_P,
    'Q': VK_Q,
    'R': VK_R,
    'S': VK_S,
    'T': VK_T,
    'U': VK_U,
    'V': VK_V,
    'W': VK_W,
    'X': VK_X,
    'Y': VK_Y,
    'Z': VK_Z,
}

vk_to_keystr = {v: k for k, v in keystr_to_vk.items()}





medium = r"""
|Esc| 1 | 2 | 3 | 4 | 5 | ` |       | = | 6 | 7 | 8 | 9 | 0 | - |
|Tab| Q | W | E | R | T | ( |       | ) | Y | U | I | O | P | \ |
|CAS| A | S | D | F | G | [ |       | ] | H | J | K | L | ; | ' |
|Sft| Z | X | C | V | B |   |       |   | N | M | , | . | / |Sft|
|Ctl|C+A|Alt|Lft|Rgt|                       | Up|Dwn| L1| L2|Win|
                      | F2|F11|   |Hom|End|
                      |   |F12|   |PgU|   |   |
                  |BkS|Del| F5|   |PgD|Ent|Spc|
"""

small = r"""
Esc  1   2   3   4   5   `         =   6   7   8   9   0   -
Tab  Q   W   E   R   T   (         )   Y   U   I   O   P   \
CAS  A   S   D   F   G   [         ]   H   J   K   L   ;   '
Sft  Z   X   C   V   B                 N   M   ,   .   /  Sft
Ctl C+A Alt Lft Rgt                        Up Dwn  L1  L2 Win
                       F2 F11   Hom End
                          F12   PgU
                  BkS Del  F5   PgD Ent Spc
"""
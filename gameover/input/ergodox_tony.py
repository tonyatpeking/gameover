from enum import Enum
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button
from gameover.input.windows_constants import *


large = r"""
+-----------------------------------------+  ·  +-----------------------------------------+
| Esc |  1  |  2  |  3  |  4  |  5  |  `  |  ·  |  =  |  6  |  7  |  8  |  9  |  0  |  -  |
|-----+-----+-----+-----+-----+-----+-----|  ·  |-----+-----+-----+-----+-----+-----+-----|
| Tab |  Q  |  W  |  E  |  R  |  T  |  ^  |  ·  |  ^  |  Y  |  U  |  I  |  O  |  P  |  \  |
|-----+-----+-----+-----+-----+-----|     |  ·  |     |-----+-----+-----+-----+-----+-----|
| CAS |  A  |  S  |  D  |  F  |  G  |  (  |  ·  |  )  |  H  |  J  |  K  |  L  |  ;  |  '  |
|-----+-----+-----+-----+-----+-----|-----|  ·  |-----|-----+-----+-----+-----+-----+-----|
| LSf |  Z  |  X  |  C  |  V  |  B  |  [  |  ·  |  ]  |  N  |  M  |  ,  |  .  |  /  | RSf |
+-----+-----+-----+-----+-----+-----+-----+  ·  +-----+-----+-----+-----+-----+-----+-----+
| Ctl | C+A | Alt | Lft | Rgt |              ·              |  Up | Dwn |  L1 |  L2 | Win |
+-----------------------------+-----------+  ·  +-----------+-----------------------------+
                              |  F2 | F11 |  ·  | Hom | End |
                        +-----|-----|-----|  ·  |-----+-----+-----+
                        |  ^  |  ^  | F12 |  ·  | PgU |  ^  |  ^  |
                        |     |     |-----|  ·  |-----|     |     |
                        | BkS | Del |  F5 |  ·  | PgD | Ent | Spc |
                        +-----------------+  ·  +-----------------+
"""


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

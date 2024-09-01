from __future__ import annotations
import rich
from colors import lerp_color


class Mode():
    all_modes: dict[str, Mode] = {}
    default_mode: None | Mode = None

    def __init__(self, name, name_short, flash_color, still_color) -> None:
        self.name = name
        self.name_short = name_short
        self.flash_color = flash_color
        self.still_color = still_color
        self.dark_color = lerp_color(still_color, '#000000', 0.8)
        self.is_active = False

    @classmethod
    def AddMode(cls, *args):
        cls.all_modes[args[0]] = Mode(*args)

    @classmethod
    def Activate(cls, mode_name):
        if mode_name in cls.all_modes:
            cls.all_modes[mode_name].is_active = True
        else:
            raise ValueError(f'Mode {mode_name} not found')

    @classmethod
    def Deactivate(cls, mode_name):
        if mode_name in cls.all_modes:
            cls.all_modes[mode_name].is_active = False
        else:
            raise ValueError(f'Mode {mode_name} not found')


Mode.AddMode('_BOSS_MODE',
             'BOSS',
             '#ffffff',
             '#9e9e9e')


Mode.AddMode('_WM_MODE',
             'WM',
             '#fa07c9',
             '#8f0a74')

Mode.AddMode('_TEXT_PROMPT_MODE',
             'PROMPT',
             '#3cfae1',
             '#208073')


Mode.AddMode('_TEXT_MODE',
             'TEXT',
             '#3cb1fa',
             '#1e6896')


Mode.AddMode('_GAMER_MODE',
             'GAME',
             '#99ee00',
             '#639903')

Mode.default_mode = Mode.all_modes['_GAMER_MODE']


def print_mode_state():
    string_builder = ''
    longest_name = max([len(mode.name_short)
                       for mode in Mode.all_modes.values()])
    for mode_name, mode in Mode.all_modes.items():
        if mode.is_active:
            color = mode.flash_color
        else:
            color = mode.dark_color

        name_short = mode.name_short.center(longest_name)
        style = f'[bold #000000 on {color}]'
        string_builder = string_builder + \
            f'{style} {name_short} [/]'
    rich.print(string_builder)


print_mode_state()

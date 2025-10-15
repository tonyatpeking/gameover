from gameover.input.hotkeys import Hotkeys, InputState, KeyState
from gameover.input.windows_constants import *
from gameover.input.keyboard_ui import KeyboardUI
from pynput.keyboard import Key, Controller
from pathlib import Path
import pyperclip
from time import sleep


def move_cursor_down_until(
    lines: list[str], cursor_line_num: int, until_prefix: str = "#"
):
    num_lines = len(lines)
    cursor_line = lines[cursor_line_num]
    while True:
        lines[cursor_line_num] = lines[cursor_line_num + 1]
        lines[cursor_line_num + 1] = cursor_line
        cursor_line_num += 1
        if cursor_line_num == num_lines - 1:
            break

        if lines[cursor_line_num + 1].startswith(until_prefix):
            break

    return lines


class TonyHotkeys:
    def __init__(self, tui: KeyboardUI, hotkeys: Hotkeys):
        self.tui = tui
        self.hotkeys = hotkeys
        self.CAS_up_allowed = True

    def CAS_up_hotkey(self, vk_code: int, is_pressed: bool, input_state: InputState):
        """
        outputs Ctrl+Alt+Shift+A IFF C+A+S is released without any other keys being pressed
        """

        CAS: set = {VK_LCONTROL, VK_LMENU, VK_LSHIFT}

        if is_pressed and vk_code not in CAS:
            self.CAS_up_allowed = False
            return

        pressed_keys = input_state.pressed_keys()

        if self.CAS_up_allowed and not is_pressed and vk_code in CAS:
            # the input state already has the vk_code released, so we add it back
            pressed_keys.add(vk_code)
            if pressed_keys == CAS:
                controller = Controller()
                with controller.pressed(Key.ctrl, Key.alt, Key.shift):
                    controller.press("a")
                    controller.release("a")
                    print("CAS+A")
                self.hotkeys.suppress()
                return

        # clear CAS state if empty keyboard
        if is_pressed == False:
            if len(pressed_keys) == 0:
                self.CAS_up_allowed = True

    def quit_app_hotkey(self, vk_code: int, is_pressed: bool, input_state: InputState):
        if is_pressed and vk_code == VK_F5:
            self.tui.exit()
            return

    def cursor_copy_down(self, vk_code: int, is_pressed: bool, input_state: InputState):
        """
        Activates when C+A+S+1 is pressed. This is shown in the tui pretty box.
        After activation, when S+9 is pressed
        1. Looks for file in the text area, if none found defaults to data.md
        2. Copies the line below <cursor> to the clipboard, selects all text, and pastes
        3. Moves cursor down until <cursor> is above a line with prefix '#' or EOF
        """
        if not hasattr(self, "cursor_copy_down_active"):
            self.cursor_copy_down_active = False
            self.tui.set_pretty_data("cursor_copy_down_active", False)

        ACTIVATION_KEYS: set = {VK_LCONTROL, VK_LMENU, VK_LSHIFT, VK_1}
        TRIGGER_KEYS: set = {VK_LSHIFT, VK_9}
        pressed_keys = input_state.pressed_keys()
        if is_pressed and pressed_keys == ACTIVATION_KEYS:
            self.cursor_copy_down_active = not self.cursor_copy_down_active
            self.tui.set_pretty_data(
                "cursor_copy_down_active", self.cursor_copy_down_active
            )

        if not self.cursor_copy_down_active:
            return

        if is_pressed and pressed_keys == TRIGGER_KEYS:

            path = Path(self.tui.text_area.text)
            if not path.exists():
                path = Path(r"G:\My Drive\Sync\Scripts\data\data.md")
            if path.exists():
                text = path.read_text()
                lines = text.split("\n")
                for line_num, line in enumerate(lines):
                    if line == "<cursor>":
                        if line_num == len(lines) - 1:
                            break

                        line_text = lines[line_num + 1]
                        print(line_text)
                        pyperclip.copy(line_text)
                        controller = Controller()
                        controller.release(Key.shift)
                        controller.release("9")

                        with controller.pressed(Key.ctrl):
                            controller.tap("a")
                        with controller.pressed(Key.ctrl):
                            controller.tap("v")
                        lines = move_cursor_down_until(lines, line_num)
                        text = "\n".join(lines)
                        path.write_text(text)
                        break
                self.hotkeys.suppress()

    def register_hotkeys(self):
        self.hotkeys.register_hardware_key_change_callback(self.CAS_up_hotkey)
        self.hotkeys.register_hardware_key_change_callback(self.cursor_copy_down)
        # self.hotkeys.register_hardware_key_change_callback(self.quit_app_hotkey)

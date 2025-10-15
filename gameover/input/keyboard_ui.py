import sys
from textual.app import App, ComposeResult
from textual.widgets import Static, Button, Label, RichLog, Pretty, TextArea
from textual.containers import Grid, Horizontal, Vertical
from textual.reactive import reactive
from gameover.input.ergodox_tony import large, keystr_to_vk
from gameover.input.windows_constants import *


from gameover.input.hotkeys import KeyState, InputState


class StdoutRedirector:
    def __init__(self, log: RichLog):
        self.log = log

    def write(self, msg):
        if msg.strip():
            self.log.write(msg)  # send to RichLog

    def flush(self):  # needed for compatibility
        pass


class KeyboardUI(App):
    CSS_PATH = "keyboard_styles.tcss"

    def compose(self) -> ComposeResult:
        self.buttons = {}
        self.logger = None
        self.pretty_box = None
        self.pretty_data = {}
        self.text_area = None
        key_type_and_content = parse_keyboard_layout(large)
        with Vertical(id="main-container"):
            with Horizontal(id="top-row"):
                with Grid(id="keyboard-grid"):
                    for key_type, key_content in key_type_and_content:
                        if key_type == "long-bottom":
                            continue
                        is_disabled = key_type == "placeholder"
                        button = Static(
                            key_content, classes=f"key {key_type}", disabled=is_disabled
                        )
                        if not is_disabled:
                            key_vk = keystr_to_vk.get(key_content, "")
                            self.buttons[key_vk] = button
                        yield button
                self.pretty_box = Pretty(self.pretty_data, id="pretty-box")
                yield self.pretty_box
            self.text_area = TextArea(id="text-area", text="test")
            yield self.text_area
            self.logger = RichLog(id="log")
            yield self.logger

    def on_mount(self):
        assert self.logger
        sys.stdout = StdoutRedirector(self.logger)
        sys.stderr = StdoutRedirector(self.logger)

    def process_hardware_key_change(
        self, vk_code: int, is_pressed: bool, input_state: InputState
    ):
        self.process_key_change(vk_code, is_pressed, input_state, False)

    def process_software_key_change(
        self, vk_code: int, is_pressed: bool, input_state: InputState
    ):
        self.process_key_change(vk_code, is_pressed, input_state, True)

    def set_pretty_data(self, key, value):
        self.pretty_data[key] = value
        self.pretty_box.update(self.pretty_data)

    def process_key_change(
        self,
        vk_code: int,
        is_pressed: bool,
        input_state: InputState,
        software_triggered: bool,
    ):
        button = self.buttons.get(vk_code, None)
        classes = ""
        if software_triggered:
            classes = "software-triggered"
        else:
            classes = "hardware-triggered"

        if button is not None:
            if is_pressed:
                button.add_class(classes)
            else:
                button.remove_class(classes)
            button.refresh()


def parse_keyboard_layout(layout_string) -> list[tuple[str, str]]:

    content_rows_only = []
    for line_num, line in enumerate(layout_string.split("\n")):
        if line.strip() == "":
            continue
        if line_num % 2 == 1:
            continue
        content_rows_only.append(line)

    def get_key_content(
        row, col, content_rows_only, do_not_recurse=False
    ) -> tuple[str, str]:
        key_type = "placeholder"
        key_content = ""

        line = content_rows_only[row]
        range_start = 1 + col * 6
        range_end = range_start + 5
        key_content = line[range_start:range_end]
        key_content = key_content.strip()

        if key_content != "":
            key_type = "normal"

        if key_content == "^":
            key_type = "long"
            # look below to get the content of the long key
            _, key_content = get_key_content(
                row + 1, col, content_rows_only, do_not_recurse=True
            )

        # look above to check if the key is bottom of a long key
        if row > 0 and key_type == "normal" and not do_not_recurse:
            above_key_type, _ = get_key_content(row - 1, col, content_rows_only)
            if above_key_type == "long":
                key_type = "long-bottom"

        return key_type, key_content

    key_type_and_content = []

    for row in range(len(content_rows_only)):
        for col in range(15):
            key_type, key_content = get_key_content(row, col, content_rows_only)
            key_type_and_content.append((key_type, key_content))

    return key_type_and_content


if __name__ == "__main__":
    app = KeyboardUI()
    app.run()
    # print(large)
    # key_type_and_content = parse_keyboard_layout(large)
    # print(key_type_and_content)

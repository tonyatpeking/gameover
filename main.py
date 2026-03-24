from gameover.input.keyboard_ui import KeyboardUI
from gameover.input.hotkeys import Hotkeys
from gameover.input.tony_hotkeys import TonyHotkeys


if __name__ == "__main__":
    tui = KeyboardUI()
    hotkeys = Hotkeys.get_instance()
    hotkeys.register_key_change_callback(
        tui.process_key_change)

    tony_hotkeys = TonyHotkeys(tui, hotkeys)
    tony_hotkeys.register_hotkeys()

    hotkeys.start_listening()
    tui.run()

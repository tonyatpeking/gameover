from gameover.input.keyboard_ui import KeyboardUI
from gameover.input.hotkeys import Hotkeys


if __name__ == "__main__":
    app = KeyboardUI()
    hotkeys = Hotkeys.get_instance()
    hotkeys.register_on_key_change(app.process_key_change)

    

    hotkeys.start_listening()
    app.run()
    


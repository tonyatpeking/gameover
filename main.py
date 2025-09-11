from gameover.input.keyboard_ui import KeyboardUI
from gameover.input.hotkeys import Hotkeys
from gameover.input.tony_hotkeys import tony_hotkeys_list




if __name__ == "__main__":
    app = KeyboardUI()
    hotkeys = Hotkeys.get_instance()
    hotkeys.register_on_hardware_key_change(app.process_key_change)

    for hotkey in tony_hotkeys_list:
        hotkeys.register_on_hardware_key_change(hotkey)
    

    hotkeys.start_listening()
    app.run()


    



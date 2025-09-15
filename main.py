from gameover.input.keyboard_ui import KeyboardUI
from gameover.input.hotkeys import Hotkeys
from gameover.input.tony_hotkeys import tony_hotkeys_list




if __name__ == "__main__":
    tui = KeyboardUI()
    hotkeys = Hotkeys.get_instance()
    hotkeys.register_hardware_key_change_callback(tui.process_hardware_key_change)
    hotkeys.register_software_key_change_callback(tui.process_software_key_change)

    for hotkey in tony_hotkeys_list:
        hotkeys.register_hardware_key_change_callback(hotkey)
    

    hotkeys.start_listening()
    tui.run()


    



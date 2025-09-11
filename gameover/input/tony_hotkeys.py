from gameover.input.hotkeys import Hotkeys
from gameover.input.windows_constants import *
from pynput.keyboard import Key, Controller

tony_hotkeys_list = []



class TonyHotkeys:
    def __init__(self):
        self.CAS_up_allowed = True
        self.hotkeys = Hotkeys.get_instance()
        pass

    def CAS_up_hotkey(self, vk_code: int, is_pressed: bool, input_state: dict[int, bool]):
        """
        outputs Ctrl+Alt+Shift+A IFF C+A+S is released without any other keys being pressed
        """

        CAS: set = {VK_LCONTROL, VK_LMENU, VK_LSHIFT}
        
        if is_pressed and vk_code not in CAS:
            self.CAS_up_allowed = False
            return

        if self.CAS_up_allowed and not is_pressed and vk_code in CAS:
            keys_pressed = {vk_code for vk_code in input_state if input_state[vk_code]}
            # the input state already has the vk_code released, so we add it back
            keys_pressed.add(vk_code)
            if keys_pressed == CAS:
                controller = Controller()
                with controller.pressed(Key.ctrl, Key.alt, Key.shift):
                    controller.press('a')
                    controller.release('a')
                    print('CAS+A')
                self.hotkeys.suppress()
                return


        # clear CAS state if empty keyboard
        if is_pressed == False:
            keys_pressed = sum(input_state.values())
            if keys_pressed == 0:
                self.CAS_up_allowed = True


tony_hotkeys = TonyHotkeys()
tony_hotkeys_list.append(tony_hotkeys.CAS_up_hotkey)


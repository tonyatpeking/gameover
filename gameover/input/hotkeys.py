import sys

from time import sleep

from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from gameover.input.ergodox_tony import vk_to_keystr

from gameover.input.windows_constants import *


def int_to_hex_str_02X(num: int) -> str:
    return f'0x{num:02X}'

def int_to_hex_str_04X(num: int) -> str:
    return f'0x{num:04X}'

class Hotkeys:
    instance = None
    def __init__(self):
        if Hotkeys.instance is not None:
            raise Exception("Hotkeys already initialized, use Hotkeys.instance instead")
        Hotkeys.instance = self
        self.keyboard_listener = keyboard.Listener(
            win32_event_filter=Hotkeys.win32_event_filter_kb
        )
        self.mouse_listener = mouse.Listener(
            win32_event_filter=Hotkeys.win32_event_filter_mouse
        )

        # input state is a dictionary of vk codes to bools (pressed or not)
        self.input_state: dict[int, bool] = {}
        NUM_VK_KEYS = 255
        for i in range(NUM_VK_KEYS):
            self.input_state[i] = False

        self.on_key_change = []


    def start_listening(self):
        self.keyboard_listener.start()
        #self.mouse_listener.start()

    def stop_listening(self):
        #self.mouse_listener.stop()
        self.keyboard_listener.stop()

    def on_hardware_key_down(self, vk_code: int):
        self.input_state[vk_code] = True
        for callback in self.on_key_change:
            callback(vk_code, True, self.input_state)

    def on_hardware_key_up(self, vk_code: int):
        self.input_state[vk_code] = False
        for callback in self.on_key_change:
            callback(vk_code, False, self.input_state)

    def register_on_key_change(self, callback):
        self.on_key_change.append(callback)

    @staticmethod
    def get_instance():
        if Hotkeys.instance is None:
            Hotkeys.instance = Hotkeys()
        return Hotkeys.instance

    @staticmethod
    def win32_event_filter_mouse(msg, data):
        hotkeys = Hotkeys.instance
        injected = bool(data.flags 
                        & (data.LLMHF_INJECTED 
                           | data.LLMHF_LOWER_IL_INJECTED)
                        )
        print(f'mouse event: {int_to_hex_str_04X(msg)}, {data} injected: {injected}')
        #hotkeys.mouse_listener.suppress_event() # type: ignore
        
        return True

    @staticmethod
    def win32_event_filter_kb(msg, data):


        
        injected = bool(data.flags 
                        & (data.LLKHF_INJECTED 
                           | data.LLKHF_LOWER_IL_INJECTED)
                        )
        
        vk_code_str = int_to_hex_str_02X(data.vkCode)
        #print(f'{vk_to_keystr[data.vkCode]} {msg} injected: {injected}')

        hotkeys = Hotkeys.instance
        assert hotkeys is not None
        if msg == WM_KEYDOWN or msg == WM_SYSKEYDOWN:
            hotkeys.on_hardware_key_down(data.vkCode)
        elif msg == WM_KEYUP or msg == WM_SYSKEYUP:
            hotkeys.on_hardware_key_up(data.vkCode)

        if data.vkCode == VK_F5:
            print('exiting')
            hotkeys.keyboard_listener.suppress_event() # type: ignore
            hotkeys.stop_listening()

        hotkeys.keyboard_listener.suppress_event() # type: ignore
        return True


if __name__ == '__main__':
    hotkeys = Hotkeys()
    hotkeys.start_listening()
    keyboard_controller = keyboard.Controller()
    mouse_controller = mouse.Controller()
    while hotkeys.keyboard_listener.running:
        sleep(0.2)
        #mouse_controller.click(mouse.Button.left)
        #mouse_controller.release(mouse.Button.left)
        #keyboard_controller.press('a')
        #keyboard_controller.release('a')

    
import sys


from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController, HotKey, GlobalHotKeys

from time import sleep

from pynput import keyboard
from gameover.input.ergodox_tony import vk_to_key_str

def vk_to_string(vk_code):
    return f'0x{vk_code:02X}'

class Hotkeys:
    instance = None
    def __init__(self):
        if Hotkeys.instance is not None:
            raise Exception("Hotkeys already initialized, use Hotkeys.instance instead")
        Hotkeys.instance = self
        self.listener = keyboard.Listener(
            win32_event_filter=Hotkeys.win32_event_filter
        )

        self.keyboard_state = {}
        NUM_VK_KEYS = 255
        for i in range(NUM_VK_KEYS):
            self.keyboard_state[vk_to_string(i)] = False


    def start_listening(self):
        self.listener.start()

    def stop_listening(self):
        self.listener.stop()

    def on_hardware_key_down(self, vk_code):
        self.keyboard_state[vk_code] = True

    def on_hardware_key_up(self, vk_code):
        self.keyboard_state[vk_code] = False

    @staticmethod
    def win32_event_filter(msg, data):

        event_type = None
        if msg == 256:
            event_type = 'key_down'
        elif msg == 257:
            event_type = 'key_up'
        elif msg == 260:
            event_type = 'sys_key_down'
        elif msg == 261:
            event_type = 'sys_key_up'
        else:
            raise Exception(f'Unknown message type: {msg}, {data.vkCode}')
        
        vk_code = vk_to_string(data.vkCode)
        print(f'{vk_to_key_str[vk_code]} {event_type}')

        hotkeys = Hotkeys.instance
        if event_type == 'key_down' or event_type == 'sys_key_down':
            hotkeys.on_hardware_key_down(vk_code)
        elif event_type == 'key_up' or event_type == 'sys_key_up':
            hotkeys.on_hardware_key_up(vk_code)

        if data.vkCode == 0x74:
            print('exiting')
            hotkeys.stop_listening()

        hotkeys.listener.suppress_event()
        return True


if __name__ == '__main__':
    hotkeys = Hotkeys()
    hotkeys.start_listening()
    while hotkeys.listener.running:
        sleep(1)

    
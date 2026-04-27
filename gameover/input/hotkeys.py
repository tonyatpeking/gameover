import sys

import time
from typing import Callable

from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode

from gameover.input.windows_constants import *
import atexit

import asyncio
import threading
from dataclasses import dataclass
AUTO_RELEASE_DELAY = 10

# vk_code, is_pressed,
#                    is_software_triggered, self.input_state_apps, self.#input_state_hardware)


@dataclass
class TriggerInfo:
    # vk_code of key that was pressed or released
    vk_code: int
    # key_str of key that was pressed or released
    key_str: str
    # pressed or released
    is_pressed: bool
    # true if the key was triggered by software
    is_software_triggered: bool
    # list of active layers
    active_layers: list[str]
    # layer that the hotkey was defined in
    defined_layer: str
    # what keys are currently pressed (according to what other apps on the system see)
    input_state_apps: InputState
    # what keys are currently presses (according to hardware)
    input_state_hardware: InputState


def int_to_hex_str_02X(num: int) -> str:
    return f"0x{num:02X}"


def int_to_hex_str_04X(num: int) -> str:
    return f"0x{num:04X}"


class KeyState:
    def __init__(self):
        self._is_pressed = False
        self._pressed_when: float | None = None
        self._auto_release_task: asyncio.Task | None = None

    def get_hotkey_loop(self) -> asyncio.AbstractEventLoop:
        return Hotkeys.get_instance().loop

    def schedule_auto_release(self, delay: float = AUTO_RELEASE_DELAY):
        loop = self.get_hotkey_loop()
        if self._auto_release_task:
            return

        def create_task():
            self._auto_release_task = loop.create_task(
                self.auto_release(delay))

        loop.call_soon_threadsafe(create_task)

    def cancel_auto_release(self):
        if self._auto_release_task:
            loop = self.get_hotkey_loop()
            loop.call_soon_threadsafe(self._auto_release_task.cancel)
            self._auto_release_task = None

    async def auto_release(self, delay: float = AUTO_RELEASE_DELAY):
        await asyncio.sleep(delay)
        self._is_pressed = False
        self._pressed_when = None
        self._auto_release_task = None
        print(f"auto released")

    @property
    def is_pressed(self):
        return self._is_pressed

    @is_pressed.setter
    def is_pressed(self, value: bool):
        self._is_pressed = value
        if value:
            self._pressed_when = time.time() if value else None
            self.schedule_auto_release()
        else:
            self.cancel_auto_release()

    @property
    def pressed_when(self):
        return self._pressed_when


class InputState(dict[int, KeyState]):
    def pressed_keys(self) -> set[int]:
        return {vk_code for vk_code in self if self[vk_code].is_pressed}


class Hotkeys:
    instance = None

    def __init__(self):
        if Hotkeys.instance is not None:
            raise Exception(
                "Hotkeys already initialized, use Hotkeys.instance instead")
        Hotkeys.instance = self

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop_runner, daemon=True)
        self.thread.start()
        self.hotkeys = {}
        self.active_layers = []

        self.keyboard_listener = keyboard.Listener(
            win32_event_filter=Hotkeys.win32_event_filter_kb
        )
        self.mouse_listener = mouse.Listener(
            win32_event_filter=Hotkeys.win32_event_filter_mouse
        )

        # input_state_apps is a dictionary of vk codes to bools (pressed or not)
        # this is what other applications see
        self.input_state_apps: InputState = InputState()
        NUM_VK_KEYS = 256
        for i in range(NUM_VK_KEYS):
            self.input_state_apps[i] = KeyState()

        # input_state_hardware is what the actual state of the hardware is
        self.input_state_hardware: InputState = InputState()
        for i in range(NUM_VK_KEYS):
            self.input_state_hardware[i] = KeyState()

        self.key_change_callbacks = []
        self.is_suppressed = False

    def loop_runner(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start_listening(self):
        self.keyboard_listener.start()
        # self.mouse_listener.start()

    def stop_listening(self):
        # self.mouse_listener.stop()
        self.keyboard_listener.stop()
        self.keyboard_listener.join()

    def update_hardware_key_state(self, vk_code: int, is_pressed: bool):
        self.input_state_hardware[vk_code].is_pressed = is_pressed

    def update_app_key_state(self, vk_code: int, is_pressed: bool):
        self.input_state_apps[vk_code].is_pressed = is_pressed

    def run_key_change_callbacks(self, vk_code: int, is_pressed: bool, is_software_triggered: bool):
        trigger_info = TriggerInfo(vk_code=vk_code,
                                   key_str=vk_to_keystr(vk_code),
                                   is_pressed=is_pressed,
                                   is_software_triggered=is_software_triggered,
                                   active_layers=self.active_layers,
                                   defined_layer="",
                                   input_state_apps=self.input_state_apps,
                                   input_state_hardware=self.input_state_hardware)
        for callback in self.key_change_callbacks:
            callback(trigger_info)

    def register_key_change_callback(self, callback: Callable[[TriggerInfo], None]):
        self.key_change_callbacks.append(callback)

    def register_hotkey(self, hotkey_str: str, callback: Callable[[TriggerInfo], None]):
        self.hotkeys[hotkey_str] = callback

    def suppress(self):
        self.is_suppressed = True
        self.keyboard_listener.suppress_event()  # type: ignore

    @staticmethod
    def get_instance():
        if Hotkeys.instance is None:
            Hotkeys.instance = Hotkeys()
        return Hotkeys.instance

    @staticmethod
    def win32_event_filter_mouse(msg, data):
        hotkeys = Hotkeys.instance
        injected = bool(
            data.flags & (data.LLMHF_INJECTED | data.LLMHF_LOWER_IL_INJECTED)
        )
        # print(f'mouse event: {int_to_hex_str_04X(msg)}, {data} injected: {injected}')
        # hotkeys.mouse_listener.suppress_event() # type: ignore

        return True

    @staticmethod
    def win32_event_filter_kb(msg, data):

        injected = bool(
            data.flags & (data.LLKHF_INJECTED | data.LLKHF_LOWER_IL_INJECTED)
        )

        vk_code_str = int_to_hex_str_02X(data.vkCode)
        # print(f'{vk_to_keystr[data.vkCode]} {msg} injected: {injected}')
        if msg not in [WM_KEYDOWN, WM_SYSKEYDOWN, WM_KEYUP, WM_SYSKEYUP]:
            print(f'unhandled keyboard event: {msg}')
            return True

        hotkeys = Hotkeys.instance
        assert hotkeys is not None

        hotkeys.is_suppressed = False
        is_pressed = msg == WM_KEYDOWN or msg == WM_SYSKEYDOWN
        if not injected:
            hotkeys.update_hardware_key_state(data.vkCode, is_pressed)

        hotkeys.run_key_change_callbacks(
            data.vkCode, msg == WM_KEYDOWN or msg == WM_SYSKEYDOWN, injected)

        if not hotkeys.is_suppressed:
            hotkeys.update_app_key_state(data.vkCode, is_pressed)

        # hotkeys.keyboard_listener.suppress_event() # type: ignore
        return True


def cleanup():
    hotkeys = Hotkeys.get_instance()
    hotkeys.stop_listening()


atexit.register(cleanup)

if __name__ == "__main__":
    hotkeys = Hotkeys()
    hotkeys.start_listening()
    keyboard_controller = keyboard.Controller()
    mouse_controller = mouse.Controller()
    while hotkeys.keyboard_listener.running:
        time.sleep(0.2)
        mouse_controller.click(mouse.Button.left)
        mouse_controller.release(mouse.Button.left)
        # keyboard_controller.press('a')
        # keyboard_controller.release('a')

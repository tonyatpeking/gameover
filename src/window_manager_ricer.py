#!/usr/bin/env python3

import os
import asyncio
import time
import aiofiles
import subprocess
from types import SimpleNamespace

FPS = 60
SLEEP_TIME = 1 / FPS
MIN_SLEEP_TIME = 0.0083

TOTAL_EFFECT_DURATION = 0.12
DEBOUNCE_TIME = 0.05
REQUEST_DEBOUNCE_TIME = 0.12

DEFAULT_START_COLOR = '#88ee00'
DEFAULT_END_COLOR = '#335533'


class WindowState:
    def __init__(self) -> None:
        self.prev_window_id = None
        self._window_id = None
        self.window_title = None
        # tag aka workspace
        self.prev_tag = None
        self._tag = None
        self.prev_monitor = None
        self._monitor = None
        self.is_fullscreen = False
        self.is_urgent = False
        self.urgent_window_id = None

    @property
    def window_id(self):
        return self._window_id

    @window_id.setter
    def window_id(self, value):
        self.prev_window_id = self._window_id
        self._window_id = value

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        self.prev_tag = self._tag
        self._tag = value

    @property
    def monitor(self):
        return self._monitor

    @monitor.setter
    def monitor(self, value):
        self.prev_monitor = self._monitor
        self._monitor = value


window_state = WindowState()


def lerp_color(start_color: str, stop_color: str, t: float) -> str:
    # Remove the '#' from the beginning of the color strings
    start_color = start_color.lstrip('#')
    stop_color = stop_color.lstrip('#')

    # Convert hex colors to RGB integers
    start_r = int(start_color[0:2], 16)
    start_g = int(start_color[2:4], 16)
    start_b = int(start_color[4:6], 16)

    stop_r = int(stop_color[0:2], 16)
    stop_g = int(stop_color[2:4], 16)
    stop_b = int(stop_color[4:6], 16)

    # Perform linear interpolation
    r = int(start_r + (stop_r - start_r) * t)
    g = int(start_g + (stop_g - start_g) * t)
    b = int(start_b + (stop_b - start_b) * t)

    # Convert back to hex and format as a color string
    return f'#{r:02X}{g:02X}{b:02X}'


def remap01(value_in_range, range_start, range_end):
    '''
    Remap value_in_range from the range [range_start,range_end] to [0,1]

    Note that a value outside the range will be linearly remapped to a value
    outside 0-1
    '''
    return (value_in_range - range_start) / (range_end - range_start)


_start_color = DEFAULT_START_COLOR
_end_color = DEFAULT_END_COLOR
_request_flash_reset = False


async def color_changer():
    last_time = time.perf_counter()
    effect_start_time = -2
    effect_end_time = -1
    final_value_set = False
    global _request_flash_reset
    while True:
        new_time = time.perf_counter()
        elapsed_time = new_time - last_time
        # do stuff

        if _request_flash_reset:
            _request_flash_reset = False
            if new_time - effect_start_time > DEBOUNCE_TIME:
                effect_start_time = new_time
                effect_end_time = effect_start_time + TOTAL_EFFECT_DURATION
                final_value_set = False

        t = remap01(new_time, effect_start_time, effect_end_time)

        if not final_value_set:
            if t > 1:
                t = 1
                final_value_set = True

            middle = lerp_color(_start_color, _end_color, t)

            subprocess.run(
                ['herbstclient', 'attr', 'theme.active.color', middle])

        # sleep for the remaining time
        after_work_time = time.perf_counter()
        work_time = after_work_time - new_time

        sleep_time_remaining = SLEEP_TIME - elapsed_time - work_time
        # print(sleep_time_remaining)
        last_time = after_work_time

        await asyncio.sleep(MIN_SLEEP_TIME)

        # if sleep_time_remaining > MIN_SLEEP_TIME:
        #     print('sleep')
        #     await asyncio.sleep(sleep_time_remaining)
        #     # time.sleep(sleep_time_remaining)




def parse_window_manager_message(message_str):
    assert message_str.startswith('WINDOW_MANAGER')
    message = SimpleNamespace()
    parts = message_str.split()
    message.event = parts[1]

    if len(parts) > 3:
        message.arg0 = parts[2]
    else:
        message.arg0 = None
    if len(parts) > 4:
        message.arg1 = ' '.join(parts[3:])
    else:
        message.arg1 = None
    return message


def process_window_manager_pipe(message_str):
    global _request_flash_reset
    message = parse_window_manager_message(message_str)
    assert message
    # https://herbstluftwm.org/herbstluftwm.html#AUTOSTART
    if message.event == 'fullscreen':
        is_fullscreen = (message.arg0 == 'on')  # 'on' or 'off'
        window_id = message.arg1
        window_state.is_fullscreen = is_fullscreen
    if message.event == 'tag_changed':
        tag = message.arg0
        monitor = message.arg1
        window_state.tag = tag
        window_state.monitor = monitor
    if message.event == 'focus_changed':
        window_id = message.arg0
        title = message.arg1
        window_state.window_id = window_id
        window_state.window_title = title
    if message.event == 'window_title_changed':
        window_id = message.arg0
        title = message.arg1
        pass
    if message.event == 'urgent':
        is_urgent = (message.arg0 == 'on')  # 'on' or 'off'
        window_id = message.arg1
        window_state.is_urgent = is_urgent
        window_state.urgent_window_id = window_id
    if message.event == 'rule':
        hook_name = message.arg0
        window_id = message.arg1
    if message.event == 'reload':
        pass
    if message.event != 'window_title_changed':
        request_flash_reset()


_request_flash_reset_prev_time = time.perf_counter()


def request_flash_reset(start_color=None, end_color=None):
    global _request_flash_reset_prev_time
    global _request_flash_reset
    global _start_color
    global _end_color
    if start_color:
        _start_color = start_color
    if end_color:
        _end_color = end_color
    current_time = time.perf_counter()
    elapsed_time = current_time - _request_flash_reset_prev_time
    if elapsed_time > REQUEST_DEBOUNCE_TIME:
        # print('window_manager_ricer: request_flash_reset')
        _request_flash_reset_prev_time = current_time
        _request_flash_reset = True
    else:
        # print('window_manager_ricer: request_flash_reset debounced')
        pass

# region Commands

def WM_FOCUS_ID(window_id):
    if window_id != None:
        subprocess.run(['herbstclient', 'jumpto', window_id])

def WM_FOCUS_UP():
    subprocess.run(['herbstclient', 'focus', 'up'])

def WM_FOCUS_DOWN():
    subprocess.run(['herbstclient', 'focus', 'down'])

# [todo] add wrap around
def WM_FOCUS_LEFT():
    subprocess.run(['herbstclient', 'focus', 'left'])

# [todo] add wrap around
def WM_FOCUS_RIGHT():
    subprocess.run(['herbstclient', 'focus', 'right'])

def WM_SHIFT_UP():
    subprocess.run(['herbstclient', 'shift', 'up'])

def WM_SHIFT_DOWN():
    subprocess.run(['herbstclient', 'shift', 'down'])

def WM_SHIFT_LEFT():
    subprocess.run(['herbstclient', 'shift', 'left'])

def WM_SHIFT_RIGHT():
    subprocess.run(['herbstclient', 'shift', 'right'])

def WM_RELOAD():
    subprocess.run(['herbstclient', 'reload'])


def WM_QUIT():
    subprocess.run(['herbstclient', 'quit'])


def WM_CLOSE_WINDOW():
    subprocess.run(['herbstclient', 'close'])


def WM_LAUNCH():
    subprocess.run(['herbstclient', 'spawn', 'rofi', '-show', 'run'])

def WM_LAUNCH_TERMINAL():
    subprocess.run(['herbstclient', 'spawn', 'kitty'])

def WM_SPLIT():
    subprocess.run(['herbstclient', 'split', 'right', '0.5' ])

def WM_REMOVE():
    subprocess.run(['herbstclient', 'remove'])

def WM_FULLSCREEN_TOGGLE():
    subprocess.run(['herbstclient', 'fullscreen', 'toggle'])

def WM_FLOAT_TOGGLE():
    subprocess.run(['herbstclient', 'set_attr', 'clients.focus.floating', 'toggle'])

resize_step = '+'+str(0.02)
def WM_RESIZE_UP():
    subprocess.run(['herbstclient', 'resize', 'up', resize_step])

def WM_RESIZE_DOWN():
    subprocess.run(['herbstclient', 'resize', 'down', resize_step])

def WM_RESIZE_LEFT():
    subprocess.run(['herbstclient', 'resize', 'left', resize_step])

def WM_RESIZE_RIGHT():
    subprocess.run(['herbstclient', 'resize', 'right', resize_step])

def WM_GOTO_WORKSPACE(workspace_id):
    subprocess.run(['herbstclient', 'use', workspace_id])

def WM_MOVE_TO_WORKSPACE(workspace_id):
    subprocess.run(['herbstclient', 'move', workspace_id])

def WM_FOCUS_PREVIOUS():
    WM_FOCUS_ID(window_state.prev_window_id)


# endregion Commands
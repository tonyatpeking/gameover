#!../.venv/bin/python

import os
import asyncio
import time
import aiofiles
import subprocess
from types import SimpleNamespace
from keymap_mode import Mode
from colors import lerp_color
from shell_utils import sh, popen
from pprint import pprint

FPS = 60
SLEEP_TIME = 1 / FPS
MIN_SLEEP_TIME = 0.0083

TOTAL_EFFECT_DURATION = 0.12
DEBOUNCE_TIME = 0.05
REQUEST_DEBOUNCE_TIME = 0.12

assert Mode.default_mode
DEFAULT_START_COLOR = Mode.default_mode.flash_color
DEFAULT_END_COLOR = Mode.default_mode.still_color


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
        print_focused_client()
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


def get_clients():
    ATTRIBUTES = [
        'class',
        'floating',
        'floating_geometry',
        'fullscreen',
        'instance',
        'pid',
        'pgid',
        'tag',
        'title',
        'urgent',
        'winid'
    ]

    # client key can be either a winid '0x...' or 'focus'
    clients_keys = []

    clients = {}
    result = sh('herbstclient attr clients', print_output=False)
    if not result:
        return clients
    lines = result.split('\n')
    for line in lines:
        line = line.strip()
        if line.endswith('.'):
            line = line[:-1]
        if line.startswith('0x') or line == 'focus':
            clients_keys.append(line)
    for client_id in clients_keys:
        client_attrs = sh('herbstclient attr clients.' +
                          client_id, print_output=False)
        clients[client_id] = {}
        if not client_attrs:
            continue
        lines = client_attrs.split('\n')
        for line in lines:
            if not '=' in line:
                continue
            line = line[6:]
            tokens = line.split('=')
            key = tokens[0]
            value = '='.join(tokens[1:])
            key = key.strip()
            value = value.strip()
            value = value.replace('"', '')
            if key in ATTRIBUTES:
                clients[client_id][key] = value
    return clients


def print_focused_client():
    clients = get_clients()
    focused_client = clients.get('focus')
    if focused_client:
        pprint(focused_client)


def get_clients_by_attr(attr, value, exact_match=True):
    clients = get_clients()
    matching_clients = {}
    for client_id, client in clients.items():
        if attr not in client:
            continue
        if exact_match and client[attr] == value:
            matching_clients[client_id] = client
        if not exact_match and value in client[attr]:
            matching_clients[client_id] = client
    return matching_clients


def get_screen_resolution():
    result = sh('herbstclient monitor_rect', print_output=False)
    if not result:
        return None
    items = result.split()
    if len(items) < 4:
        return None
    width = int(items[2])
    height = int(items[3])
    return (width, height)


# region Commands


def WM_BRING(window_id):
    '''
    Bring the window to the current tag and focuses it
    '''
    if window_id != None:
        subprocess.run(['herbstclient', 'bring', window_id])


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
    subprocess.run(['herbstclient', 'split', 'right', '0.5'])


def WM_REMOVE():
    subprocess.run(['herbstclient', 'remove'])


def WM_FULLSCREEN_TOGGLE():
    subprocess.run(['herbstclient', 'fullscreen', 'toggle'])


def WM_FLOAT_TOGGLE():
    subprocess.run(['herbstclient', 'set_attr',
                   'clients.focus.floating', 'toggle'])


def WM_FLOAT(to_float: str):
    '''
    to_float = 'true' or 'false'
    '''
    subprocess.run(['herbstclient', 'set_attr',
                   'clients.focus.floating', 'true'])


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


def WM_TOGGLE_VOLUME_CONTROL():
    WM_TOGGLE_FLOATING_CONSOLE_PROGRAM('pulsemixer', 800, 600)


def WM_TOGGLE_TOP_CONTROL():
    WM_TOGGLE_FLOATING_CONSOLE_PROGRAM('btop', 1280, 720)


def WM_TOGGLE_FLOATING_CONSOLE_PROGRAM(program_name: str, width, height):
    visibility_var_name = f'_{program_name}_visible'

    def set_visible(value):
        setattr(WM_TOGGLE_FLOATING_CONSOLE_PROGRAM, visibility_var_name, value)

    def is_visible():
        return getattr(WM_TOGGLE_FLOATING_CONSOLE_PROGRAM, visibility_var_name)

    if not hasattr(WM_TOGGLE_FLOATING_CONSOLE_PROGRAM, visibility_var_name):
        set_visible(False)

    title = f'{program_name}_floating_console'
    console_clients = get_clients_by_attr('title', title)
    if not console_clients:
        sh(f'kitty --title {title} --detach sh -c {program_name} &')
        time.sleep(0.4)
        console_clients = get_clients_by_attr('title', title)
        set_visible(False)
    if not console_clients:
        print(f'Failed to launch {program_name}')
        return
    client = list(console_clients.values())[0]
    winid = client['winid']

    if is_visible():
        set_visible(False)
        sh(f'herbstclient set_attr clients.{winid}.minimized true')
    else:
        set_visible(True)
        WM_BRING(winid)
        sh(f'herbstclient set_attr clients.{winid}.minimized false')
        sh(f'herbstclient set_attr clients.{winid}.floating true')
        resolution = get_screen_resolution()
        offset_x = 200
        offset_y = 200
        if resolution:
            screen_width, screen_height = resolution
            # center the window
            offset_x = (screen_width - width) // 2
            offset_y = (screen_height - height) // 2

        sh(f'herbstclient set_attr clients.{winid}.floating_geometry {
           width}x{height}+{offset_x}+{offset_y}')
# endregion Commands

#!../.venv/bin/python

import pyperclip
import os
import asyncio
import aiofiles
from pathlib import Path
import time
import sys
import window_manager_ricer
import inspect
from types import SimpleNamespace
from colors import *
from keymap_mode import Mode, print_mode_state
from types import SimpleNamespace
import pprint
from shell_utils import sh
import subprocess
import xnview_rater
import macros

DEBUG_PRINT_RAW_LINES = False
DEBUG_PRINT_GAMER_MESSAGE_RAW = False
DEBUG_PRINT_WINDOW_MANAGER_RAW = False
DEBUG_PRINT_ENTER = True
DEBUG_PRINT_EXIT = True
DEBUG_PRINT_COMMAND = True
DEBUG_PRINT_MODE_BEFORE = True
DEBUG_PRINT_MODE_AFTER = True

GAMER_MESSAGE_PIPE = Path('/tmp/gamer_message_pipe')
WINDOW_MANAGER_PIPE = Path('/tmp/window_manager_pipe')


# Ensure the pipe exists
if not os.path.exists(WINDOW_MANAGER_PIPE):
    os.mkfifo(WINDOW_MANAGER_PIPE)


# This is the time the pipe watcher will sleep before checking the pipe again
# AFTER the pipe has been successfully read, thus it is the minimum time
# between reads.
# It is NOT the latency of the pipe watcher as it will almost immediately
# process the pipe the first time it is read, using `async with aiofiles.open`
PIPE_WATCHER_SLEEP_TIME = 0.1


def reload_script():
    # sleep before reload so if we have a infinite loop we can manually stop it
    time.sleep(0.3)
    print("--- gameover.py reloading ---")
    # get the current script path
    script_path = Path(__file__).resolve()
    # kill the current script and start it again
    os.execv(sys.executable, [sys.executable, str(script_path)])


while not GAMER_MESSAGE_PIPE.exists():
    print(f"Waiting for pipe to start {GAMER_MESSAGE_PIPE}")
    time.sleep(0.5)


def make_pipe_watcher(pipe_path, process_message_fn, sleep_time):
    async def read_pipe():
        while True:
            if not pipe_path.exists():
                print(f"Waiting for pipe to start {pipe_path}")
                await asyncio.sleep(0.5)
            else:
                break
        async with aiofiles.open(pipe_path, 'r') as fifo:
            while True:
                # Read a line from the pipe asynchronously
                lines = await fifo.read()
                if lines:
                    if DEBUG_PRINT_RAW_LINES:
                        print(f'#### lines ####:\n{lines}')
                    for line in lines.splitlines():
                        try:
                            process_message_fn(line.strip())
                        except Exception as e:
                            print(f'Error processing message: {line}')
                            print_colorized_exception(e)
                await asyncio.sleep(sleep_time)
    return read_pipe


def get_commands(module=None):
    if not module:
        module = sys.modules[__name__]
    name_function_pairs = inspect.getmembers(module, inspect.isfunction)
    commands = {}
    for name, function in name_function_pairs:
        if name.isupper():
            # Do something with the function
            commands[name] = function
    return commands


def parse_gamer_message(message_str):
    message = SimpleNamespace()
    message.kwargs = {}
    parts = message_str.split()
    message.type = parts[0]
    if len(parts) == 1:
        message.value = None
        message.kwargs = {}
        return message
    message.value = parts[1]
    for arg in parts[2:]:
        key, value = arg.split('=')
        message.kwargs[key] = value
    return message


def flash_top_mode():
    top_mode = None
    for mode in Mode.all_modes.values():
        if mode.is_active:
            top_mode = mode
            break
    if top_mode:
        window_manager_ricer.request_flash_reset(
            top_mode.flash_color, top_mode.still_color)


def process_gamer_message_pipe(message_str):
    if DEBUG_PRINT_MODE_BEFORE:
        print_mode_state()

    if DEBUG_PRINT_GAMER_MESSAGE_RAW:
        print(f'>>> raw message: {message_str}')
    message = parse_gamer_message(message_str)
    if message.type == 'ENTER':
        if DEBUG_PRINT_ENTER:
            print(message_str)
        mode_name = message.value
        if mode_name in Mode.all_modes:
            mode = Mode.all_modes[mode_name]
            mode.is_active = True
            window_manager_ricer.request_flash_reset(
                mode.flash_color, mode.still_color)
    if message.type == 'EXIT':
        if DEBUG_PRINT_EXIT:
            print(message_str)
        mode_name = message.value
        if mode_name in Mode.all_modes:
            mode = Mode.all_modes[mode_name]
            mode.is_active = False
        flash_top_mode()
    if message.type == 'COMMAND':
        if DEBUG_PRINT_COMMAND:
            print(message_str)
        command = message.value

        gameover_commands = get_commands()
        if command in gameover_commands:
            gameover_commands[command](**message.kwargs)

        # relay commands to window manager ricer
        window_manager_commands = get_commands(window_manager_ricer)
        if command in window_manager_commands:
            window_manager_commands[command](**message.kwargs)

        # relay commands to xnview rater
        xnview_rater_commands = get_commands(xnview_rater)
        if command in xnview_rater_commands:
            xnview_rater_commands[command](**message.kwargs)

        # relay commands to macros
        macros_commands = get_commands(macros)
        if command in macros_commands:
            macros_commands[command](**message.kwargs)

    if DEBUG_PRINT_MODE_AFTER:
        print_mode_state()
    print()


async def main():
    gamer_commands_pipe_watcher = make_pipe_watcher(
        GAMER_MESSAGE_PIPE,
        process_gamer_message_pipe,
        PIPE_WATCHER_SLEEP_TIME)

    window_manager_pipe_watcher = make_pipe_watcher(
        WINDOW_MANAGER_PIPE,
        window_manager_ricer.process_window_manager_pipe,
        PIPE_WATCHER_SLEEP_TIME)

    read_gamer_commands_task = asyncio.create_task(
        gamer_commands_pipe_watcher())

    read_window_manager_task = asyncio.create_task(
        window_manager_pipe_watcher())

    color_changer_task = asyncio.create_task(
        window_manager_ricer.color_changer())

    await asyncio.gather(read_window_manager_task, read_gamer_commands_task, color_changer_task)


# region xrandr
def run_xrandr():
    try:
        # Run the xrandr command and capture its output
        result = subprocess.run(
            ['xrandr'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running xrandr: {e}")
        print(f"Error output: {e.stderr}")


class DisplayInfo(SimpleNamespace):
    name: str
    max_resolution: str | None
    refresh_rates: list[str] | None
    current_refresh_rate: str | None
    preferred_refresh_rate: str | None


def parse_xrandr_output(xrandr_output):
    connected_displays = []
    lines = xrandr_output.splitlines()
    for line_idx, line in enumerate(lines):
        if " connected " in line:
            display_info = DisplayInfo()
            display_info.name = line.split()[0]
            if line_idx+1 < len(lines):
                next_line_items = lines[line_idx+1].split()
                display_info.max_resolution = next_line_items[0]
                display_info.refresh_rates = []
                for refresh_rate in next_line_items[1:]:
                    is_current = False
                    is_preferred = False
                    if '+' in refresh_rate:
                        is_preferred = True
                        refresh_rate = refresh_rate.replace('+', '')
                    if '*' in refresh_rate:
                        is_current = True
                        refresh_rate = refresh_rate.replace('*', '')
                    display_info.refresh_rates.append(refresh_rate)
                    if is_current:
                        display_info.current_refresh_rate = refresh_rate
                    if is_preferred:
                        display_info.preferred_refresh_rate = refresh_rate

            # display.highest_resolution = line
            connected_displays.append(display_info)
    return connected_displays

# endregion


# region Commands

def RELOAD_GAMEOVER():
    reload_script()


def CHANGE_INPUT_LANGUAGE():
    if CHANGE_INPUT_LANGUAGE.current_language == 'us':
        CHANGE_INPUT_LANGUAGE.current_language = 'cn'
        print('Language: Chinese')
        sh('ibus engine "libpinyin"')
    else:
        CHANGE_INPUT_LANGUAGE.current_language = 'us'
        print('Language: English')
        sh('ibus engine "xkb:us::eng"')


CHANGE_INPUT_LANGUAGE.current_language = 'us'

_current_brightness = 1
_brightness_step = 0.1


def SCREENSHOT():
    sh('flameshot gui')


def BRIGHTNESS(value):
    displays = parse_xrandr_output(run_xrandr())
    print(f'Changing brightness to {value}')
    for display_info in displays:
        sh(f'xrandr --output {display_info.name} --brightness {value}')


def BRIGHTNESS_UP():
    global _current_brightness
    _current_brightness += _brightness_step
    BRIGHTNESS(_current_brightness)


def BRIGHTNESS_DOWN():
    global _current_brightness
    _current_brightness -= _brightness_step
    BRIGHTNESS(_current_brightness)

# endregion


if __name__ == "__main__":
    asyncio.run(main())

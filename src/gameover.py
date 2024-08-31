#!../venv/bin/python

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

DEBUG_PRINT_GAMER_MESSAGE_RAW = True
DEBUG_PRINT_WINDOW_MANAGER_RAW = False
DEBUG_PRINT_ENTER = True
DEBUG_PRINT_EXIT = False
DEBUG_PRINT_COMMAND = True

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
                continue
            async with aiofiles.open(pipe_path, 'r') as fifo:
                # Read a line from the pipe asynchronously
                lines = await fifo.read()
                for line in lines.splitlines():
                    process_message_fn(line.strip())
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
    message.value = parts[1]
    for arg in parts[2:]:
        key, value = arg.split('=')
        message.kwargs[key] = value
    return message


def process_gamer_message_pipe(message_str):
    if DEBUG_PRINT_GAMER_MESSAGE_RAW:
        print(f'>>> raw message: {message_str}')
    message = parse_gamer_message(message_str)
    if message.type == 'ENTER':
        if DEBUG_PRINT_ENTER:
            print(message_str)
        mode = message.value

        if mode == '_WINDOW_MANAGER_MODE':
            window_manager_ricer.request_flash_reset(
                COLOR_WINDOW_MODE_FLASH, COLOR_WINDOW_MODE_STILL)
        if mode == '_TEXT_MODE':
            window_manager_ricer.request_flash_reset(
                COLOR_TM_FLASH, COLOR_TM_STILL)
        if mode == '_BOSS_MODE':
            window_manager_ricer.request_flash_reset(
                COLOR_BM_FLASH, COLOR_BM_STILL)
        if mode == '_GAMER_MODE':
            window_manager_ricer.request_flash_reset(
                COLOR_GM_FLASH, COLOR_GM_STILL)
    if message.type == 'EXIT':
        if DEBUG_PRINT_EXIT:
            print(message_str)
        pass
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

    await asyncio.gather(read_window_manager_task)


# region Commands

def RELOAD_GAMEOVER():
    reload_script()

# endregion


if __name__ == "__main__":
    asyncio.run(main())

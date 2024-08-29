#!../venv/bin/python

import pyperclip
import os
import asyncio
import aiofiles
from pathlib import Path
import time
import sys
import window_manager_ricer


GAMER_COMMANDS_PIPE = Path('/tmp/gamer_commands_pipe')
WINDOW_MANAGER_PIPE = Path('/tmp/window_manager_pipe')

# Ensure the pipe exists
if not os.path.exists(WINDOW_MANAGER_PIPE):
    os.mkfifo(WINDOW_MANAGER_PIPE)


# This is the time the pipe watcher will sleep before checking the pipe again
# AFTER the pipe has been successfully read, thus it is the minimum time
# between reads.
# It is NOT the latency of the pipe watcher as it will almost immediately
# process the pipe the first time it is read, using `async with aiofiles.open`
PIPE_WATCHER_SLEEP_TIME = 0.01


def reload_script():
    # sleep before reload so if we have a infinite loop we can manually stop it
    time.sleep(1)
    print("Reloading script")
    # get the current script path
    script_path = Path(__file__).resolve()
    # kill the current script and start it again
    os.execv(sys.executable, [sys.executable, str(script_path)])


while not GAMER_COMMANDS_PIPE.exists():
    print(f"Waiting for pipe to start {GAMER_COMMANDS_PIPE}")
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


async def read_gamer_commands_pipe():
    while True:
        if not GAMER_COMMANDS_PIPE.exists():
            print(f"Waiting for pipe to start {GAMER_COMMANDS_PIPE}")
            await asyncio.sleep(0.5)
            continue
        async with aiofiles.open(GAMER_COMMANDS_PIPE, 'r') as fifo:
            # Read a line from the pipe asynchronously
            lines = await fifo.read()
            for line in lines.splitlines():
                print(f"{line.strip()}")
        await asyncio.sleep(.1)


async def read_window_manager_pipe():
    while True:
        if not WINDOW_MANAGER_PIPE.exists():
            print(f"Waiting for pipe to start {WINDOW_MANAGER_PIPE}")
            await asyncio.sleep(0.5)
            continue
        async with aiofiles.open(WINDOW_MANAGER_PIPE, 'r') as fifo:
            # Read a line from the pipe asynchronously
            lines = await fifo.read()
            for line in lines.splitlines():
                print(f"{line.strip()}")
        await asyncio.sleep(.1)


def process_gamer_commands_pipe(message):
    print(message)
    if message.startswith('ENTER'):
        mode = message.split(' ')[1]
        if mode == '_WINDOW_MANAGER_MODE':
            window_manager_ricer.request_flash_reset('#fa07c9', '#5c194e')
        if mode == '_TEXT_MODE':
            window_manager_ricer.request_flash_reset('#94e9f7', '#30555c')
        if mode == '_BOSS_MODE':
            window_manager_ricer.request_flash_reset('#ffffff', '#9e9e9e')
        if mode == '_GAMER_MODE':
            window_manager_ricer.request_flash_reset('#88ee00', '#335533')


async def main():
    gamer_commands_pipe_watcher = make_pipe_watcher(
        GAMER_COMMANDS_PIPE,
        process_gamer_commands_pipe,
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

if __name__ == "__main__":
    asyncio.run(main())

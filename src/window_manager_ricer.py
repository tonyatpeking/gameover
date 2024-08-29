#!/usr/bin/env python3

import os
import asyncio
import time
import aiofiles
import subprocess


FPS = 60
SLEEP_TIME = 1 / FPS
MIN_SLEEP_TIME = 0.0083

TOTAL_EFFECT_DURATION = 0.12
DEBOUNCE_TIME = 0.05
REQUEST_DEBOUNCE_TIME = 0.12

DEFAULT_START_COLOR = '#88ee00'
DEFAULT_END_COLOR = '#335533'


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


def process_window_manager_pipe(message):
    global _request_flash_reset
    print(message)
    if message:
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
        print('window_manager_ricer: request_flash_reset')
        _request_flash_reset_prev_time = current_time
        _request_flash_reset = True

#!../.venv/bin/python
from pathlib import Path
import yaml
import os
from colors import print_colorized_exception
import asyncio
import pyperclip
from pprint import pprint
import path_utils
from path_utils import FileType
from rating_folders import Rating, rating_to_folder
import time
import rich

WAIT_BEFORE_CLIPBOARD_COPY = 0.05
DOUBLE_TAP_TIME = 0.5
RATING_CACHE_FILE = Path('/home/tony/Work/gameover/ratings.yaml')


rating_cache = {

    #     'parent': {
    #         'file': 'rating'
    #     }

}


def dump_ratings_file():
    with open(RATING_CACHE_FILE, 'w') as file:
        yaml.dump(rating_cache, file, sort_keys=False, allow_unicode=True)
    print(f'Rating cache dumped to {RATING_CACHE_FILE}')


def load_ratings_file():
    with open(RATING_CACHE_FILE, 'r') as file:
        rating_cache = yaml.load(file, Loader=yaml.FullLoader)
    return rating_cache


def _xn_rate_path(path: Path, rating: Rating):

    parent = str(path.parent)

    if parent not in rating_cache:
        rating_cache[parent] = {}
    if rating == Rating.C:
        if path.name in rating_cache[parent]:
            del rating_cache[parent][path.name]
    else:
        rating_cache[parent][path.name] = rating.value


async def try_xn_rate_clipboard_path(rating: str):
    await asyncio.sleep(WAIT_BEFORE_CLIPBOARD_COPY)
    clip = pyperclip.paste()
    # check if clip is a valid path
    try:
        path = Path(clip)
        if not path.exists():
            return
        _xn_rate_path(path, Rating(rating))
        # pprint(rating_cache, indent=2)
        dump_ratings_file()
    except Exception as e:
        print_colorized_exception(e)


async def try_xn_sort_by_type():
    await asyncio.sleep(WAIT_BEFORE_CLIPBOARD_COPY)
    clip = pyperclip.paste()
    try:
        path = Path(clip)
        if not path.exists():
            return
        if path.is_dir():
            dir = path
        elif path.is_file():
            dir = path.parent
        for file in dir.iterdir():
            _xn_rate_path(file, Rating.SortByType)
        dump_ratings_file()
    except Exception as e:
        print_colorized_exception(e)


def print_summary_of_files_to_move():
    global rating_cache
    rating_cache = load_ratings_file()
    rating_summary = {}
    for parent, files in rating_cache.items():
        rating_summary[parent] = {}
        for file, rating in files.items():
            filetype = path_utils.get_filetype(file)
            folder = rating_to_folder(rating, filetype)
            if folder not in rating_summary[parent]:
                rating_summary[parent][folder] = 0
            rating_summary[parent][folder] += 1
    rich.print('[bold on #004477]      SUMMARY      [/]')
    pprint(rating_summary, indent=2)
    rich.print('[bold on #004477]      SUMMARY      [/]')


def move_rated_to_dir():
    print('move_rated_to_dir')


def move_rated_to_dir_sequence():
    '''
    Single Tap: Print a summary of files that will be moved.
    Double Tap: Only move files if this is triggered twice within DOUBLE_TAP_TIME.
    '''
    if not hasattr(move_rated_to_dir_sequence, 'last_tap_time'):
        move_rated_to_dir_sequence.last_tap_time = 0

    current_time = time.time()

    if current_time - move_rated_to_dir_sequence.last_tap_time < DOUBLE_TAP_TIME:
        # Double tap detected
        move_rated_to_dir()  # Function to move files
    else:
        # Single tap detected
        print_summary_of_files_to_move()  # Function to print summary

    move_rated_to_dir_sequence.last_tap_time = current_time


def XN_RATE_CLIPBOARD_PATH(rating: str):
    asyncio.create_task(try_xn_rate_clipboard_path(rating))


def XN_SORT_BY_TYPE():
    asyncio.create_task(try_xn_sort_by_type())


def XN_MOVE_RATED_TO_DIR():
    move_rated_to_dir_sequence()


def XN_DUMP_RATINGS_FILE():
    dump_ratings_file()


def XN_LOAD_RATINGS_FILE():
    global rating_cache
    rating_cache = load_ratings_file()


if __name__ == '__main__':
    print(rating_cache)
    print('saving')
    # dump_rating_cache()

    print('loading')
    rating_cache_loaded = load_ratings_file()
    print(rating_cache_loaded)

    # assert rating_cache == rating_cache_loaded
    try:
        raise Exception('test')
    except Exception as e:
        print_colorized_exception(e)

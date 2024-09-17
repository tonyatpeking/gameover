#!../.venv/bin/python
from pathlib import Path
import yaml
import os
from colors import print_colorized_exception, get_color, colorize_substring
import asyncio
import pyperclip
from pprint import pprint
import path_utils
from path_utils import FileType
from rating_folders import Rating, rating_to_subfolder, is_sort_by_type_folder
import time
import rich
from pydantic import BaseModel
from collections import deque
import shutil
WAIT_BEFORE_CLIPBOARD_COPY = 0.05
DOUBLE_TAP_TIME = 0.5
RATING_CACHE_FILE = Path('/home/tony/Work/gameover/ratings.yaml')


class RatingCache:
    def __init__(self, ratings_filepath: Path):
        '''
        Schema:
        {
            'parent_dir': {
                'file1': 'rating',
                'file2': 'rating',
                ...
            },
            ...
        }
        '''
        self.ratings_file = ratings_filepath
        self._rating_cache = {}

    def dump(self):
        with open(self.ratings_file, 'w') as file:
            yaml.dump(self._rating_cache, file,
                      sort_keys=False, allow_unicode=True)
        print(f'Rating cache dumped to {self.ratings_file}')

    def load(self):
        with open(self.ratings_file, 'r') as file:
            self._rating_cache = yaml.load(file, Loader=yaml.FullLoader)
            if self._rating_cache is None:
                self._rating_cache = {}
        print(f'Rating cache loaded from {self.ratings_file}')

    def is_rating_file_empty(self):
        with open(self.ratings_file, 'r') as file:
            read_file = yaml.load(file, Loader=yaml.FullLoader)
            if read_file is None or read_file == {}:
                return True
            return False

    def rate_path(self, path: Path, rating: Rating):
        parent = str(path.parent)
        if parent not in self._rating_cache:
            self._rating_cache[parent] = {}
        if rating == Rating.C:
            if path.name in self._rating_cache[parent]:
                del self._rating_cache[parent][path.name]
        else:
            self._rating_cache[parent][path.name] = rating.value

    def clear_cache(self):
        self._rating_cache = {}
        self.dump()


rating_cache: RatingCache = RatingCache(RATING_CACHE_FILE)


class RatingSummary:
    def __init__(self, rating_cache: RatingCache):
        '''
        Schema:
        {
            'parent_dir': {
                (rating, filetype): count,
                (rating, filetype): count,
                ...
            },
            ...
        }
        '''
        self.rating_summary = {}
        for parent, files in rating_cache._rating_cache.items():
            self.rating_summary[parent] = {}
            for file, rating in files.items():
                file_full_path = Path(parent) / file
                filetype = path_utils.get_filetype(file_full_path)
                rating_filetype = (Rating(rating), filetype)
                if rating_filetype not in self.rating_summary[parent]:
                    self.rating_summary[parent][rating_filetype] = 0
                self.rating_summary[parent][rating_filetype] += 1

    def print_summary(self):
        rich.print('[bold on #004477]      SUMMARY      [/]')
        if not self.rating_summary:
            rich.print('[bold on #008877]      NO RATINGS      [/]')
        for parent, folders in self.rating_summary.items():
            rich.print(f'[{get_color(FileType.Dir)}]{parent}[/]')
            entries = []
            for (rating, filetype), count in folders.items():
                foldername_colored = rating_to_subfolder(
                    rating, filetype, colorize=True)
                rating_color = get_color(rating)
                if not foldername_colored:
                    foldername_colored = f'Will not move {rating} {filetype}'
                entry = f'{foldername_colored} : [{rating_color}]{count}[/]'
                entries.append(entry)
            entries = sorted(entries, key=lambda x: x[0])
            for entry in entries:
                rich.print(f'    {entry}')

        rich.print('[bold on #004477]      END SUMMARY      [/]')


def _xn_rate_path(path: Path, rating: Rating):
    rating_cache.rate_path(path, rating)


async def try_xn_rate_clipboard_path(rating: str):
    await asyncio.sleep(WAIT_BEFORE_CLIPBOARD_COPY)
    clip = pyperclip.paste()
    # check if clip is a valid path
    try:
        paths = [Path(path) for path in clip.split('\n')]
        for path in paths:
            if not path.exists():
                continue
            _xn_rate_path(path, Rating(rating))
            # pprint(rating_cache, indent=2)
    except Exception as e:
        print_colorized_exception(e)


async def try_xn_sort_by_type():
    await asyncio.sleep(WAIT_BEFORE_CLIPBOARD_COPY)
    clip = pyperclip.paste()
    try:
        for line in clip.split('\n'):
            path = Path(clip)
            if not path.exists():
                return
            if path.is_dir():
                dir = path
            elif path.is_file():
                dir = path.parent
            for file in dir.iterdir():
                _xn_rate_path(file, Rating.SortByType)
    except Exception as e:
        print_colorized_exception(e)


def move_rated_to_dir():

    # [(from, to), (from, to), ...]
    from_to = deque()

    for parent, files in rating_cache._rating_cache.items():
        parent = Path(parent)
        target_parent = parent
        parent_name = parent.name
        if is_sort_by_type_folder(parent_name):
            target_parent = parent.parent

        for file, rating in files.items():

            from_path = parent / file
            filetype = path_utils.get_filetype(from_path)
            rating = Rating(rating)

            to_path = target_parent / \
                rating_to_subfolder(rating, filetype) / file

            if filetype == FileType.Dir:
                from_to.appendleft((from_path, to_path))
            else:
                from_to.append((from_path, to_path))

    # pprint(from_to)
    for from_path, to_path in from_to:
        if not to_path.parent.exists():
            os.makedirs(to_path.parent)
        shutil.move(from_path, to_path.parent)
    rating_cache.clear_cache()


def move_rated_to_dir_sequence():
    '''
    Single Tap: Print a summary of files that will be moved.
    Double Tap: Only move files if this is triggered twice within DOUBLE_TAP_TIME.
    '''
    if not hasattr(move_rated_to_dir_sequence, 'last_tap_time',):
        move_rated_to_dir_sequence.last_tap_time = 0

    current_time = time.time()

    if current_time - move_rated_to_dir_sequence.last_tap_time < DOUBLE_TAP_TIME:
        # Double tap detected
        move_rated_to_dir()  # Function to move files
    else:
        # Single tap detected

        rating_cache.dump()

        rating_summary = RatingSummary(rating_cache)
        rating_summary.print_summary()

    move_rated_to_dir_sequence.last_tap_time = current_time


def XN_RATE_CLIPBOARD_PATH(rating: str):
    asyncio.create_task(try_xn_rate_clipboard_path(rating))


def XN_SORT_BY_TYPE():
    asyncio.create_task(try_xn_sort_by_type())


def XN_MOVE_RATED_TO_DIR():
    move_rated_to_dir_sequence()


def XN_DELETE_UNRATED():
    pass


def XN_DUMP_RATINGS_FILE():
    rating_cache.dump()


def XN_LOAD_RATINGS_FILE():
    rating_cache.load()
    rating_summary = RatingSummary(rating_cache)
    rating_summary.print_summary()


if __name__ == '__main__':
    pass
    # print(rating_cache)
    # print('saving')
    # # dump_rating_cache()

    # print('loading')
    # rating_cache_loaded = load_ratings_file()
    # print(rating_cache_loaded)

    # # assert rating_cache == rating_cache_loaded
    # try:
    #     raise Exception('test')
    # except Exception as e:
    #     print_colorized_exception(e)

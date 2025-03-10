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
from rating_folders import Rating, rating_to_subfolder, is_filetype_folder, is_rating_folder
import time
import rich
from pydantic import BaseModel
from collections import deque
import shutil
from config import GAMEOVER_DIR
from rich.tree import Tree


WAIT_BEFORE_CLIPBOARD_COPY = 0.05
DOUBLE_TAP_TIME = 0.5


RATING_CACHE_FILE = GAMEOVER_DIR / 'xnview_rater' / 'ratings.yaml'
# create the folder if it doesn't exist
RATING_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

ACTION_BUFFER_FILE = GAMEOVER_DIR / 'xnview_rater' / 'actions.yaml'
ACTION_BUFFER_FILE.parent.mkdir(parents=True, exist_ok=True)


class RatingCache:
    def __init__(self, ratings_filepath: Path):
        '''
        Schema:
        {
            'parent_dir': {
                'file1': 'rating folder',
                'file2': 'rating folder',
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

    def rate_path(self, path: Path, rating: Rating, filetype: FileType | str = 'auto'):
        parent = str(path.parent)
        if parent not in self._rating_cache:
            self._rating_cache[parent] = {}
        if rating == Rating.C:
            if path.name in self._rating_cache[parent]:
                del self._rating_cache[parent][path.name]
        else:
            if filetype == 'auto':
                filetype = path_utils.get_filetype(path)
            rating_folder = rating_to_subfolder(rating, filetype)
            self._rating_cache[parent][path.name] = rating_folder

    def clear_cache(self):
        self._rating_cache = {}
        self.dump()

    def move_rated_to_dir(self):

        # [(from, to), (from, to), ...]
        from_to = deque()

        for parent, files in self._rating_cache.items():
            parent = Path(parent)
            target_parent = parent
            parent_name = parent.name
            if is_rating_folder(parent_name):
                target_parent = parent.parent

            for file, rating_folder in files.items():

                from_path = parent / file
                to_path = target_parent / \
                    rating_folder / file
                filetype = path_utils.get_filetype(from_path)
                # process dirs last
                if filetype == FileType.Dir:
                    from_to.appendleft((from_path, to_path))
                else:
                    from_to.append((from_path, to_path))
        # pprint(from_to)
        for from_path, to_path in from_to:
            try:
                if not to_path.parent.exists():
                    os.makedirs(to_path.parent)
                if to_path.parent.name == rating_to_subfolder(Rating.Face, filetype):
                    shutil.copy(from_path, to_path.parent)
                else:
                    shutil.move(from_path, to_path.parent)
            except Exception as e:
                print(f'Error moving {from_path} to {to_path}')
                print_colorized_exception(e)
        self.clear_cache()


rating_cache: RatingCache = RatingCache(RATING_CACHE_FILE)


class RatingSummary:
    def __init__(self, rating_cache: RatingCache):
        '''
        Schema:
        {
            'parent_dir': {
                rating_dir: count,
                rating_dir: count,
                ...
            },
            ...
        }
        '''
        self.rating_summary = {}
        for parent, files in rating_cache._rating_cache.items():
            self.rating_summary[parent] = {}
            for _, rating_folder in files.items():
                if rating_folder not in self.rating_summary[parent]:
                    self.rating_summary[parent][rating_folder] = 0
                self.rating_summary[parent][rating_folder] += 1

    def print_summary(self):
        rich.print('[bold on #004477]      SUMMARY      [/]')
        if not self.rating_summary:
            rich.print('[bold on #008877]      NO RATINGS      [/]')
        for parent, folders in self.rating_summary.items():
            rich.print(f'[{get_color(FileType.Dir)}]{parent}[/]')
            entries = []
            for rating_folder, count in folders.items():

                entry = f'{rating_folder} : {count}'
                entries.append(entry)
            entries = sorted(entries, key=lambda x: x[0])
            for entry in entries:
                rich.print(f'    {entry}')

        rich.print('[bold on #004477]      END SUMMARY      [/]')


class ActionBuffer:
    def __init__(self, buffer_filepath: Path):
        '''
        Schema:
        {
            'action':  'action',
            'from': ['path/to/file1', 'path/to/file2', ...],
            'to': ['path/to/file1', 'path/to/file2', ...],
        }
        '''
        self.buffer_file = buffer_filepath
        self.buffer = {}

    def set_action(self, action: str):
        self.buffer['action'] = action

    def set_from(self, from_path: list[Path]):
        self.buffer['from'] = from_path

    def set_to(self, to_path: list[Path]):
        self.buffer['to'] = to_path

    def clear(self):
        self.buffer = {}

    def dump(self):
        with open(self.buffer_file, 'w') as file:
            yaml.dump(self.buffer, file, sort_keys=False, allow_unicode=True)
        print(f'Action buffer dumped to {self.buffer_file}')

    def load(self):
        with open(self.buffer_file, 'r') as file:
            self.buffer = yaml.load(file, Loader=yaml.FullLoader)
            if self.buffer is None:
                self.buffer = {}
        print(f'Action buffer loaded from {self.buffer_file}')

    def make_summary_tree(self):
        tree = Tree('Action Buffer')


action_buffer = ActionBuffer(ACTION_BUFFER_FILE)


async def try_xn_rate_clipboard_path(rating: str):
    try:
        paths = await get_clipboard_paths()
        for path in paths:
            rating_cache.rate_path(path, Rating(rating))
            # pprint(rating_cache, indent=2)
    except Exception as e:
        print_colorized_exception(e)


async def try_xn_rate_clipboard_image_set(rating: str):
    try:
        paths = await get_clipboard_paths()
        for path in paths:
            set_dir = None
            filetype = path_utils.get_filetype(path)
            if filetype == FileType.Dir:
                set_dir = path
            elif filetype == FileType.Image:
                set_dir = path.parent
            else:
                raise Exception(f'Unsupported filetype: {filetype}')

            if is_rating_folder(set_dir.name):
                set_dir = set_dir.parent

            rating_cache.rate_path(set_dir, Rating(rating), FileType.Image)
            # pprint(rating_cache, indent=2)
    except Exception as e:
        print_colorized_exception(e)


async def get_clipboard_paths():
    await asyncio.sleep(WAIT_BEFORE_CLIPBOARD_COPY)
    clip = pyperclip.paste()
    paths = [Path(path) for path in clip.split('\n')]
    for path in paths:
        if not path.exists():
            continue
    return paths


async def try_xn_set_from_buffer():
    try:
        paths = await get_clipboard_paths()
        action_buffer.set_from(paths)
    except Exception as e:
        print_colorized_exception(e)


async def try_xn_set_to_buffer():
    try:
        paths = await get_clipboard_paths()
        action_buffer.set_to(paths)
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
                rating_cache.rate_path(file, Rating.SortByType)
    except Exception as e:
        print_colorized_exception(e)


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
        rating_cache.move_rated_to_dir()  # Function to move files
    else:
        # Single tap detected
        rating_cache.dump()
        rating_summary = RatingSummary(rating_cache)
        rating_summary.print_summary()
    move_rated_to_dir_sequence.last_tap_time = current_time


def XN_RATE_CLIPBOARD_SET(rating: str):
    asyncio.create_task(try_xn_rate_clipboard_image_set(rating), name='XN_RATE_CLIPBOARD_SET')


def XN_RATE_CLIPBOARD_PATH(rating: str):
    asyncio.create_task(try_xn_rate_clipboard_path(rating), name='XN_RATE_CLIPBOARD_PATH')


def XN_SORT_BY_TYPE():
    asyncio.create_task(try_xn_sort_by_type(), name='XN_SORT_BY_TYPE')


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


def XN_UNIFY_RATING_FOLDERS():
    pass


def XN_SET_FROM_BUFFER():
    pass


def XN_SET_TO_BUFFER():
    pass


def XN_DUMP_ACTIONS():
    pass


def XN_RUN_ACTIONS():
    pass


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

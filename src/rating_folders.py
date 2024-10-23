import os
import stat
import shutil
from pathlib import Path
import traceback
from path_utils import FileType
from enum import Enum
from colors import get_color
# ------- config ----------

ROOT_DIR = Path(r'C:\Tony\Downloads\Chrome\AI ehentai aas110 laoshi')


class Rating(Enum):
    SS = 'SS'
    S = 'S'
    A = 'A'
    B = 'B'
    C = 'C'
    Face = 'Face'
    SortByType = 'SortByType'


rating_to_folder_map = {
    FileType.Image: {
        Rating.SS: (1, 'P', 'SS'),
        Rating.S: (2, 'P', 'S'),
        Rating.A: (3, 'P', 'A'),
        Rating.B: (4, 'P', 'B'),
        Rating.SortByType: (8, 'P', None),
        Rating.Face: (12, 'P', 'Face'),
    },
    FileType.Video: {
        Rating.SS: (5, 'V', 'SS'),
        Rating.S: (6, 'V', 'S'),
        Rating.A: (7, 'V', 'A'),
        Rating.B: (11, 'V', 'B'),
        Rating.SortByType: (9, 'V', None),
        Rating.Face: (13, 'V', 'Face'),
    },
    FileType.Dir: {
        Rating.SS: (None, None, '_SS'),
        Rating.S: (None, None, '_S'),
        Rating.A: (None, None, '_A'),
        Rating.B: (None, None, '_B'),
    },
    FileType.Compressed: {
        Rating.SortByType: (10, 'Compressed', None),
    },
}


def is_filetype_folder(folder: str) -> bool:
    video_sort_by_type_folders = rating_to_subfolder(
        Rating.SortByType, FileType.Video)
    image_sort_by_type_folders = rating_to_subfolder(
        Rating.SortByType, FileType.Image)
    return folder == video_sort_by_type_folders or folder == image_sort_by_type_folders


def is_rating_folder(folder: str):
    if not hasattr(is_rating_folder, 'rating_folders'):
        is_rating_folder.rating_folders = set()
        for filetype in rating_to_folder_map:
            for rating in rating_to_folder_map[filetype]:
                rating_folder = rating_to_subfolder(rating, filetype)
                is_rating_folder.rating_folders.add(rating_folder)
    return folder in is_rating_folder.rating_folders


NO_SUBFOLDER = ''
SEPARATOR = ' - '

def rating_to_subfolder(rating: Rating | str, filetype: FileType | str, colorize=False) -> str:
    if isinstance(rating, str):
        rating = Rating(rating)
    if isinstance(filetype, str):
        filetype = FileType(filetype)

    number = None
    filetype_char = None
    rating_char = None

    if filetype not in rating_to_folder_map:
        return NO_SUBFOLDER

    if rating not in rating_to_folder_map[filetype]:
        return NO_SUBFOLDER

    number, filetype_char, rating_char = rating_to_folder_map[filetype][rating]

    if colorize:
        filetype_color = get_color(filetype)
        if filetype_char is not None:
            filetype_char = f'[{filetype_color}]{filetype_char}[/]'
        rating_color = get_color(rating)
        if rating_char is not None:
            rating_char = f'[{rating_color}]{rating_char}'
    string_builder = [number, filetype_char, rating_char]
    # remove None
    string_builder = [str(x) for x in string_builder if x is not None]

    return SEPARATOR.join(string_builder)


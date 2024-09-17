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
    SortByType = 'SortByType'


rating_to_folder_map = {
    FileType.Image: {
        Rating.SS: (1, 'P', 'SS'),
        Rating.S: (2, 'P', 'S'),
        Rating.A: (3, 'P', 'A'),
        Rating.B: (4, 'P', 'B'),
        Rating.SortByType: (8, 'P', None),
    },
    FileType.Video: {
        Rating.SS: (5, 'V', 'SS'),
        Rating.S: (6, 'V', 'S'),
        Rating.A: (7, 'V', 'A'),
        Rating.B: (11, 'V', 'B'),
        Rating.SortByType: (9, 'V', None),
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


def is_sort_by_type_folder(folder: str) -> bool:
    video_sort_by_type_folders = rating_to_subfolder(
        Rating.SortByType, FileType.Video)
    image_sort_by_type_folders = rating_to_subfolder(
        Rating.SortByType, FileType.Image)
    return folder == video_sort_by_type_folders or folder == image_sort_by_type_folders


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


# old_folders = ['S', 'A', 'B', '_SS', '_S', '_A', '_B']
# old_to_new_translation_p = {
#     'SS': PSS,
#     'S': PS,
#     'A': PA,
#     'B': PB,
#     'P': P,
#     'V': V,
#     'img': P,
#     'video': V,
#     '_SS': PSS,
#     '_S': PS,
#     '_A': PA,
#     '_B': PB,
# }
# old_to_new_translation_v = {
#     'SS': VSS,
#     'S': VS,
#     'A': VA,
#     'B': VB,
#     'P': P,
#     'V': V,
#     'img': P,
#     'video': V,
#     '_SS': VSS,
#     '_S': VS,
#     '_A': VA,
#     '_B': VB,
# }

# FOLDERS_P = [PSS, PS, PA, PB]
# FOLDERS_PV = [PSS, PS, PA, PB, VSS, VS, VA]
# FOLDERS_PVB = [PSS, PS, PA, PB, VSS, VS, VA, VB]
# FOLDERS_ALL = [PSS, PS, PA, PB, VSS, VS, VA, VB, P, V, OTHER]

# OLD_TO_NEW_TRANSLATION = old_to_new_translation_p
# FOLDERS = FOLDERS_P
# SOFT = False


# # folders = ['_S', '_A', '_B']
# ignore_prefix = '_____'
# IGNORE_DIRS = ['__SSS', '__Template',
#                '__Search', '___Sorted', '__A', '__B', '__S', '_A', '_B', '_S', '_SS', '_SSS', '_Template']
# IGNORE_DIRS.extend(FOLDERS_ALL)

# LEVEL = 1  # 0 for root dir, 1 for 1 level down etc


# def run():
#     paths_to_make_folders = [ROOT_DIR]
#     print(paths_to_make_folders)

#     for _ in range(LEVEL):
#         paths_deeper = []
#         for parent_paths in paths_to_make_folders:
#             paths_deeper.extend(
#                 [x for x in parent_paths.iterdir() if x.is_dir()])
#         paths_to_make_folders = paths_deeper

#     if SOFT:
#         for p in paths_to_make_folders:
#             print(p)


# def make_folders_for_path(path_to_make_folders):
#     print(f'Making folders for: {str(path_to_make_folders)} ')
#     for folder in FOLDERS:
#         path_to_folder = path_to_make_folders.joinpath(folder)
#         if os.path.exists(path_to_folder):
#             continue
#         if not SOFT:
#             os.mkdir(path_to_folder)
#         else:
#             pass
#         print(f'[{folder}] ', end='')
#     print('')


# def rename_folders_for_username(username):
#     for old_folder, new_folder in OLD_TO_NEW_TRANSLATION.items():
#         path_to_old_folder = username.joinpath(old_folder)
#         if (path_to_old_folder.exists()):
#             path_to_new_folder = username.joinpath(new_folder)
#             print(f'Renaming folders for: {str(username)}', end=' ')
#             print(f'{old_folder} -> {new_folder}')
#             if SOFT:
#                 continue
#             try:
#                 os.renames(path_to_old_folder, path_to_new_folder)
#             except:
#                 print('WARNING: Could not rename folder')


# def make_folders():
#     for path_to_make_folders in paths_to_make_folders:
#         folder_name = str(path_to_make_folders.name)
#         if (folder_name in IGNORE_DIRS):
#             print(f'ignoring folder: {folder_name}')
#             continue

#         rename_folders_for_username(path_to_make_folders)

#         try:
#             make_folders_for_path(path_to_make_folders)
#         except:
#             print(f'could not make folder for {path_to_make_folders}')
#             print(traceback.format_exc())


# # make_folders()
# # print( username_paths )

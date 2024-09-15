import os
import stat
import shutil
from pathlib import Path
import traceback
from path_utils import FileType
from enum import Enum
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
        Rating.SS: '1 - P - SS',
        Rating.S: '2 - P - S',
        Rating.A: '3 - P - A',
        Rating.B: '4 - P - B',
        Rating.SortByType: '8 - P',
    },
    FileType.Video: {
        Rating.SS: '5 - V - SS',
        Rating.S: '6 - V - S',
        Rating.A: '7 - V - A',
        Rating.B: '11 - V - B',
        Rating.SortByType: '9 - V',
    },
    FileType.Dir: {
        Rating.SS: '_SS',
        Rating.S: '_S',
        Rating.A: '_A',
        Rating.B: '_B',
    },
}

OTHER = '10 - Other'
NO_SUBFOLDER = ''


def rating_to_folder(rating: Rating | str, filetype: FileType | str) -> str:
    if isinstance(rating, str):
        rating = Rating(rating)
    if isinstance(filetype, str):
        filetype = FileType(filetype)

    if filetype not in rating_to_folder_map:
        return OTHER
    if rating not in rating_to_folder_map[filetype]:
        return NO_SUBFOLDER
    return rating_to_folder_map[filetype][rating]


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

import os
import pathlib
from pathlib import Path
from typing import Iterator
import re
from enum import Enum

# common operations
# os.rename(_from, _to)
# os.path.join(root_path, path)
# os.makedirs(name, exist_ok=True)
# os.listdir(root_path) # only returns dir name, not full path
# os.path.splitext(filepath)
# glob.glob("*.jpg"):
# recursively make dirs
# Path(filepath).mkdir(parents=True)

IMAGE_SUFFIXES = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.ppm', '.tiff', '.tif', '.jfif', '.tga']
VIDEO_SUFFIXES = ['.mp4', '.avi', '.mov', '.wmv',
                  '.flv', '.mkv', '.webm', '.m4v', '.vid', '.ts']
COMPRESSED_SUFFIXES = ['.zip', '.rar', '.7z', '.tar', '.gz', '.z']


class FileType(Enum):
    Image = 'image'
    Video = 'video'
    Compressed = 'compressed'
    Unknown = 'unknown'
    Dir = 'dir'


def get_filetype(filename: Path | str) -> FileType:
    """Returns the filetype of a file.

    Parameters
    ----------
    filename : Path
        The path of the file.

    Returns
    -------
    filetype : str
        The filetype of the file.
    """
    if isinstance(filename, str):
        filename = Path(filename)
    if filename.is_dir():
        return FileType.Dir
    suffix = filename.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return FileType.Image
    elif suffix in VIDEO_SUFFIXES:
        return FileType.Video
    elif suffix in COMPRESSED_SUFFIXES:
        return FileType.Compressed
    else:
        return FileType.Unknown


def get_all_dirs_recursive(path):
    for p in path.iterdir():
        if p.is_dir():
            yield p
            yield from get_all_dirs_recursive(p)


def remove_empty_folders(path, do_not_remove_folders_list, remove_root=True):
    'Function to remove empty folders'
    if not os.path.isdir(path):
        return

    if os.path.basename(path) in do_not_remove_folders_list:
        return

  # remove empty subfolders
    files = os.listdir(path)
    if len(files):
        for f in files:
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                remove_empty_folders(fullpath, do_not_remove_folders_list)

  # if folder empty, delete it
    files = os.listdir(path)
    if len(files) == 0 and remove_root:
        print("Removing empty folder:", path)
        os.rmdir(path)


def list_files(path: Path, suffixes=None):
    files = [f for f in path.iterdir() if f.is_file()]
    if suffixes:
        files = [f for f in files if f.suffix.lower() in suffixes]
    return files


def list_dirs(path: Path):
    return [f for f in path.iterdir() if f.is_dir()]


def list_videos(path: Path):
    return list_files(path, VIDEO_SUFFIXES)


def list_images(path: Path):
    return list_files(path, IMAGE_SUFFIXES)


def list_all_file_names(path, full_path=False, has_prefix=None, suffixes=None):
    all_file_names = os.listdir(path)
    if has_prefix:
        all_file_names = [
            p for p in all_file_names if p.startswith(has_prefix)]
    if not full_path:
        return all_file_names
    return [os.path.abspath(os.path.join(path, p)) for p in all_file_names]


def list_full_dirs(root_path):
    '''
    list the full directories
    ignores files and links
    '''
    paths = os.listdir(root_path)
    paths = [os.path.join(root_path, path) for path in paths]
    paths = [path for path in paths if os.path.isdir(path)]
    return paths


def move_all_files_to_dir(source_dir, target_dir):
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)
    file_names = list_all_file_names(source_dir)
    for file_name in file_names:
        try:
            source_full_path = source_dir / file_name
            target_full_path = target_dir / file_name
            source_full_path.rename(target_full_path)
        except Exception as e:
            print(
                f'failed to move file {file_name} \nfrom {source_dir} \nto {target_dir}')
            print(e)


def get_last_part_of_path(path):
    return os.path.basename(os.path.normpath(path))


def output_all_file_names(path, output_filename, ignore):
    filenames = list_all_file_names(path)
    filenames = [filename for filename in filenames if filename not in ignore]
    with open(output_filename, 'w') as f:
        for filename in filenames:
            f.write("%s\n" % filename)


def rename_folder_recursively(old_path, new_path):
    try:
        os.renames(old_path, new_path)
    except:
        print('failed to rename the following')
        print(str(old_path) + '  to')
        print(new_path)
        print('')


def get_extention(filepath):
    return pathlib.Path(filepath).suffix


def iter_dir_tree(source_root: str | Path,
                  whitelist_folders: list[str] = []) -> Iterator[Path]:
    """
    Recursively iterates through all items in a directory tree

    Parameters
    ----------
    source_root : str | Path
    whitelist_folders : list[str], optional, by default []
        see map_dir_tree for description

    Yields
    -------
    Iterator[Path]
    """
    source_root = Path(source_root)
    glob_strings = []
    if len(whitelist_folders) > 0:
        for folder in whitelist_folders:
            glob_strings.append(f'**/{folder}/**')
    else:
        glob_strings = ['**/*']
    for glob_string in glob_strings:
        for child_path in source_root.glob(glob_string):
            yield child_path


def map_dir_tree(source_root: str | Path,
                 mapped_root: str | Path,
                 whitelist_folders: list[str] = []) -> Iterator[tuple[Path, Path]]:
    """
    Recursively maps entire folder tree from source to mapped.
    Only returns mappings, does not actually move or create files.

    Parameters
    ----------
    source_root : str | Path

    mapped_root : str | Path

    whitelist_folders : list[str], optional, by default []
        If any part of path contains whitelist folder, then it will count as
        whitelisted, e.g. for whitelist of ['_SS'], Path('1/2/3/_SS/3/2/1') 
        will be whitelisted.
        If left as empty, will not use whitelists and return all subfolder/files

    Yields
    -------
    tuple[source_path:Path, mapped_path:Path]

    """
    mapped_root = Path(mapped_root)
    source_root = Path(source_root)

    for source_path in iter_dir_tree(source_root, whitelist_folders):
        relative_path = source_path.relative_to(source_root)
        mapped_path = mapped_root / relative_path
        yield source_path, mapped_path


def clean_filename(dirty: str) -> str:
    clean = re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", dirty)
    return clean


def write_list_to_file(lst, filepath):
    with open(filepath, 'w') as f:
        for item in lst:
            f.write(f'{item}\n')


def make_dirs(*, filepath=None, dirpath=None, skip_on_warning=False):
    # the first * argument is to force keyword arguments
    if filepath:
        path = Path(filepath)
        suffix = path.suffix
        if not suffix:
            print(f'Warning: file {filepath} has no suffix', end='')
            if skip_on_warning:
                print(', skipping')
                return
            else:
                print(', making dir anyway')
        path.parent.mkdir(parents=True, exist_ok=True)
    elif dirpath:
        path = Path(dirpath)
        suffix = path.suffix
        if suffix:
            print(f'Warning: dir {dirpath} has suffix', end='')
            if skip_on_warning:
                print(', skipping')
                return
            else:
                print(', making dir anyway')
        path.mkdir(parents=True, exist_ok=True)
    else:
        pass


def test_make_dirs():
    # should make 1
    make_dirs(filepath=r'C:\Tony\Test\filepath\1\2.txt')

    # should make 11\22 with warning
    make_dirs(filepath=r'C:\Tony\Test\filepath\11\22\33')

    # should warn and skip 44\55
    make_dirs(filepath=r'C:\Tony\Test\filepath\44\55', skip_on_warning=True)

    # should make 1\2.txt with warning
    make_dirs(dirpath=r'C:\Tony\Test\dirpath\1\2.txt')

    # should make 11\22
    make_dirs(dirpath=r'C:\Tony\Test\dirpath\11\22')

    # should warn and skip 44\55.txt
    make_dirs(dirpath=r'C:\Tony\Test\dirpath\44\55.txt', skip_on_warning=True)


if __name__ == '__main__':
    pass
    # print(clean_filename(r'[HEY-094]Amateur Girl with Tasty Body : Rin Miura'))
    # for source, mapped in map_dir_tree(r'G:\My Drive\S\__hentai\Abgrund (Saikawa Yusa)', r'G:\My Drive\S\__hentai\Abgrund (Saikawa Yusa)c'):
    #     if source.is_dir():
    #         print(source)

    #         print(mapped)
    # test_make_dirs()

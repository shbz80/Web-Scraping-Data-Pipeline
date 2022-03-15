"""This module implements some useful util functions and classes
"""
import os
from os import listdir, walk
from os.path import isfile, join
# some constants
PAGE_SLEEP_TIME = 0.5
TIME_OUT = 15

# some functions
def create_dir_if_not_exists(dir: str) -> bool:
    """Creates a directory at the given path if it doesn't exist

    Args:
        dir (str): path for directory       

    Returns:
        bool: if the directory was created (True) or if it already 
        existed (False)
    """
    try:
        os.mkdir(dir)
        return True
    except FileExistsError:
        print(f'The directory "{dir}" exists')
        return False

def get_list_of_files(dir: str) -> list[str]:
    """Get a list of file in the given dir"""
    if not os.path.isdir(dir):
        raise Exception('Not a vald directory.')

    return [f for f in listdir(dir)
                     if isfile(join(dir, f))]

def get_list_of_dirs(dir: str) -> list[str]:
    """Get a list of dirs in the given dir"""
    return next(walk(dir))[1]

def is_dir_present(dir, path):
    """Does the given dir exis in the given path(dir)"""
    return dir in get_list_of_dirs(path)

def is_file_present(file, path):
    """Does the given file exis in the given path(dir)"""
    return file in get_list_of_files(path)

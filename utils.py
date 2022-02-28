"""This module implements some useful util functions and classes
"""
import os

# some constants
PAGE_SLEEP_TIME = 1.5

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

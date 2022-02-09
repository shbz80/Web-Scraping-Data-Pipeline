
import os

def create_dir_if_not_exists(dir):
    try:
        os.mkdir(dir)
        return True
    except FileExistsError:
        print(f'The directory "{dir}"" exists')
        return False

import os

def create_directory_at(dir_path):
    """
    Creates a directory of with path dir_path
    """
    if type(dir_path) is not str:
        raise TypeError('Directory path should be a string.')

    try:
        os.mkdir(dir_path)
    except FileExistsError:
        print('Directory already exists. Not creating a new one.')
    except Exception as e:
        print(e)

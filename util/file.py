import os
from typing import List, Any


def exists_file(file):
    return os.path.isfile(file)


def exists_dir(dir):
    return os.path.exists(dir) and not os.path.isfile(dir)


def file_dir(filename):
    return os.path.dirname(filename)

def file_name(filename):
    return os.path.basename(filename)

def file_name_noext(filename):
    name = os.path.basename(filename)
    return os.path.splitext(name)[0]

def file_name_ext(filename):
    name = os.path.basename(filename)
    name_arr = os.path.splitext(name)
    return name_arr[0], name_arr[1] if len(name_arr) > 1 else ''

def file_ext(filename):
    name = os.path.basename(filename)
    name_arr = os.path.splitext(name)
    return name_arr[1] if len(name_arr) > 1 else ''


def mkdir(dir):
    if not exists_dir(dir):
        os.makedirs(dir)
    return dir

if __name__ == '__main__':
    # print(os.path.dirname(r'D:/232/121/2323.tx'))
    pass

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

def file_name_ext(filename):
    name =file_name(filename)
    name_arr = os.path.splitext(name)
    return name_arr[0], name_arr[1] if len(name_arr) > 1 else ''


def mkdir(dir):
    if not exists_dir(dir):
        os.makedirs(dir)
    return dir

def walk_and_select(path, select_fn):
    res = []
    assert os.path.isdir(path), f'path({path}) is expected as a dir'
    assert select_fn is not None
    for root, dirs, files in os.walk(path):
        listed_files = [os.path.join(root, f) for f in files]
        # print(f'root:{root}, files:{files}')
        for f in listed_files:
            if select_fn(f):
                res.append(f)
    return res

if __name__ == '__main__':
    # print(os.path.dirname(r'D:/232/121/2323.tx'))
    # fs = walk_and_select(r'../translated', lambda x: x.endswith('.rpy'))
    # for f in fs: print(f)
    # print(file_dir(r'../translated\tmp\mytr\NikiEvents_bak.rpy'))
    pass

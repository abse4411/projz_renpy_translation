# projz_renpy_translation, a translator for RenPy games
# Copyright (C) 2023  github.com/abse4411
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging
import os

from .os_info import is_windows


def exists_file(file):
    return os.path.isfile(file)


def exists_dir(dir):
    return os.path.exists(dir) and not os.path.isfile(dir)


def file_dir(filename):
    return os.path.dirname(filename)


def file_name(filename):
    return os.path.basename(filename)


def file_name_ext(filename):
    name, ext = os.path.splitext(file_name(filename))
    return name, ext


def default_open(file, mode, encoding='utf-8', **kwargs):
    return open(file, mode, encoding=encoding, **kwargs)


def default_read(file, **kwargs):
    return default_open(file, 'r')


def default_write(file, newline='\n', **kwargs):
    return default_open(file, 'w', newline=newline, **kwargs)


def mkdir(dir):
    if not exists_dir(dir):
        os.makedirs(dir)
    return dir


def walk_and_select(root, select_fn=None, exclude_dirs=None):
    assert os.path.isdir(root), f'{root} is expected as a dir'
    res_files = []
    mapped_dirs = []
    if exclude_dirs is not None:
        for d in exclude_dirs:
            p = os.path.join(root, d)
            if exists_dir(p):
                mapped_dirs.append(p)

    def _isexcluded(sd):
        for ed in mapped_dirs:
            if os.path.samefile(sd, ed):
                return False
        return True

    stack = [root]
    while stack:
        current_dir = stack.pop()
        for item in os.listdir(current_dir):
            item_path = os.path.join(current_dir, item)
            if os.path.isfile(item_path) and select_fn(item_path):
                res_files.append(item_path)
            elif os.path.isdir(item_path) and _isexcluded(item_path):
                stack.append(item_path)
    return res_files


def open_and_select(fn: str):
    if (not exists_file(fn)) and (not exists_dir(fn)):
        return
    try:
        if is_windows():
            fn = fn.replace('/', '\\')
            os.system(f'explorer /select,{fn}')
    except Exception as e:
        logging.exception(e)

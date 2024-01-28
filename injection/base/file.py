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
import shutil

from injection.base import BaseInjector
from util import exists_file, file_dir, file_name, exists_dir


class FileInjector(BaseInjector):
    def __init__(self, source_filename: str, target_filename: str):
        self.source_filename = source_filename
        self.target_filename = target_filename

    def __call__(self):
        logging.info(f'Copying {self.source_filename} to {self.target_filename}')
        shutil.copy(self.source_filename, self.target_filename)
        return True

    def undo(self):
        if exists_file(self.target_filename):
            logging.info(f'Deleting {self.target_filename}')
            os.remove(self.target_filename)
        return True


class PyFileInjector(BaseInjector):
    def __init__(self, source_filename: str, target_filename: str):
        self.source_filename = source_filename
        self.target_filename = target_filename

    def __call__(self):
        logging.info(f'Copying {self.source_filename} to {self.target_filename}')
        shutil.copy(self.source_filename, self.target_filename)
        return True

    def undo(self):
        if exists_file(self.target_filename):
            logging.info(f'Deleting {self.target_filename}')
            os.remove(self.target_filename)
        filename, ext = os.path.splitext(self.target_filename)
        ext = ext.lower()
        if ext == '.py':
            # pyo file before Python 3.5
            pyo_file = filename + '.pyo'
            if exists_file(pyo_file):
                logging.info(f'Deleting pyo file: {pyo_file}')
                os.remove(pyo_file)
            pycache_dir = os.path.join(file_dir(filename), '__pycache__')
            true_name = file_name(filename)
            if exists_dir(pycache_dir):
                items = os.listdir(pycache_dir)
                for i in items:
                    names = i.split('.')
                    if names and names[0] == true_name and names[-1] == 'pyc':
                        pyc = os.path.join(pycache_dir, i)
                        logging.info(f'Deleting pyc file: {pyc}')
                        os.remove(pyc)
                        break
        return True


class RpyFileInjector(BaseInjector):
    def __init__(self, source_filename: str, target_filename: str):
        self.source_filename = source_filename
        self.target_filename = target_filename

    def __call__(self):
        logging.info(f'Copying {self.source_filename} to {self.target_filename}')
        shutil.copy(self.source_filename, self.target_filename)
        return True

    def undo(self):
        if exists_file(self.target_filename):
            logging.info(f'Deleting {self.target_filename}')
            os.remove(self.target_filename)
        filename, ext = os.path.splitext(self.target_filename)
        ext = ext.lower()
        if ext == '.rpy':
            # rpyc file
            rpyc_file = filename + '.rpyc'
            if exists_file(rpyc_file):
                logging.info(f'Deleting pyo file: {rpyc_file}')
                os.remove(rpyc_file)
        return True

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

import yaml

from util import default_read, mkdir

CONFIG_FILE = './config.yaml'


class ProjzConfig:
    GLOBAL_SEC = 'projz'
    ENABLE_LOG = False
    CONSOLE_LOG = False
    LOG_PATH = './projz/log'
    LOG_LEVEL = 'ERROR'
    PROJECT_PATH = './projz'
    TMP_PATH = './projz/tmp'
    WRITE_CACHE_SIZE = 500
    REMOVE_MARKS = False
    REMOVE_TAGS = False
    NUM_WORKERS = 2

    def __init__(self, config_file):
        self.log = logging.getLogger(__name__)
        try:
            with default_read(CONFIG_FILE) as f:
                cfg = yaml.safe_load(f)
            self.cfg = cfg
        except Exception as e:
            print(f'An error occurred while loading config file ({config_file}):{e}')
            logging.exception(e)
            self.cfg = None

    def __getitem__(self, key: str):
        return self.cfg[self.GLOBAL_SEC].get(key, None)

    @property
    def enable_log(self):
        if self.cfg:
            return self['log']['enable']
        return self.ENABLE_LOG

    @property
    def console_log(self):
        if self.cfg:
            return self['log']['console']
        return self.CONSOLE_LOG

    @property
    def log_path(self):
        if self.cfg:
            return self['log']['path']
        return self.LOG_PATH

    @property
    def log_level(self):
        if self.cfg:
            return self['log']['level']
        return self.LOG_LEVEL

    @property
    def tmp_path(self):
        if self.cfg:
            return self['tmp_path']
        return self.TMP_PATH

    @property
    def num_workers(self):
        if self.cfg:
            return self['num_workers']
        return self.NUM_WORKERS

    @property
    def project_path(self):
        if self.cfg:
            return self['project_path']
        return self.PROJECT_PATH

    @property
    def write_cache_size(self):
        if self.cfg:
            return self['index']['write_cache_size']
        return self.WRITE_CACHE_SIZE

    @property
    def remove_marks(self):
        if self.cfg:
            return self['remove_marks']
        return self.REMOVE_MARKS

    @property
    def remove_tags(self):
        if self.cfg:
            return self['remove_tags']
        return self.REMOVE_TAGS


default_config = ProjzConfig(CONFIG_FILE)
mkdir(default_config.log_path)
mkdir(default_config.project_path)
mkdir(default_config.tmp_path)

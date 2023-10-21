import distutils
import logging

import configparser

from util.file import exists_file

CONFIG_FILE = './config.ini'


class config:
    GLOBAL_SEC = 'GLOBAL'
    LOG_PATH = './projz/log'
    PROJECT_PATH = './projz'
    REMOVE_MARKS = False
    REMOVE_TAGS = False
    NUM_WORKERS = 2
    def __init__(self, config_file):
        self.log = logging.getLogger(__name__)
        try:
            cfg = configparser.ConfigParser()
            assert exists_file(config_file), f'config file {config_file} not found'
            cfg.read(config_file)
            self.cfg = cfg
        except Exception as e:
            self.log.error(f'An error occurred while loading config file ({config_file}):{e}')
            self.cfg = None

    @property
    def log_path(self):
        if self.cfg:
            return self.get_global('LOG_PATH')
        return self.LOG_PATH

    @property
    def num_workers(self):
        if self.cfg:
            return int(self.get_global('NUM_WORKERS'))
        return self.NUM_WORKERS

    @property
    def project_path(self):
        if self.cfg:
            return self.get_global('PROJECT_PATH')
        return self.PROJECT_PATH

    @property
    def remove_marks(self):
        if self.cfg:
            return distutils.util.strtobool(self.get_global('REMOVE_MARKS'))
        return self.REMOVE_MARKS

    @property
    def remove_tags(self):
        if self.cfg:
            return distutils.util.strtobool(self.get_global('STRIP_TAGS'))
        return self.REMOVE_TAGS

    def get_global(self, key: str):
        return self.get(self.GLOBAL_SEC, key)

    def get(self, sec: str, key: str):
        if self.cfg.has_option(sec, key):
            return self.cfg.get(sec, key)
        return None


default_config = config(CONFIG_FILE)

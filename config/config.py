import logging

import configparser

CONFIG_FILE = './config.ini'


class config:
    GLOBAL_SEC = 'GLOBAL'
    LOG_PATH = './projz/log'
    PROJECT_PATH = './projz'

    def __init__(self, config_file):
        self.log = logging.getLogger(__name__)
        try:
            cfg = configparser.ConfigParser()
            cfg.read(config_file)
            self.cfg = cfg
        except Exception as e:
            self.log.error(f'An error occurred while loading config file ({config_file}):{e}')

    @property
    def log_path(self):
        if self.cfg:
            return self.get_global('LOG_PATH')
        return self.log_path

    @property
    def project_path(self):
        if self.cfg:
            return self.get_global('PROJECT_PATH')
        return self.log_path

    def get_global(self, key: str):
        return self.get(self.GLOBAL_SEC, key)

    def get(self, sec: str, key: str):
        if self.cfg.has_option(sec, key):
            return self.cfg.get(sec, key)
        return None


default_config = config(CONFIG_FILE)

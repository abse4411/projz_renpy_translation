import json
import logging
from pathlib import Path
from typing import Any

from util import default_read, default_write, exists_file

_ui_config_file = r'./_ui_config.json'


class UiConfig:
    def __init__(self, filename):
        self._data = {
            'theme': 'default_dark.xml',
            'language': 'en',
            'dir_history': []
        }
        self._filename = filename
        try:
            if exists_file(self._filename):
                with default_read(self._filename) as f:
                    self._data = json.load(f)
        except Exception as e:
            logging.exception(e)

    def save(self):
        try:
            with default_write(self._filename) as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.exception(e)

    def put(self, key, value):
        self._data[key] = value

    def list_append(self, key, value):
        old_list = self.list_of(key, None)
        if old_list is not None:
            old_list.append(value)

    def dict_update(self, key: str, value: dict):
        old_dict = self.dict_of(key, None)
        if old_dict is not None:
            old_dict.update(value)

    def list_append_and_save(self, key, value: Any):
        self.list_append(key, value)
        self.save()

    def dict_update_and_save(self, key, value: dict):
        self.dict_update(key, value)
        self.save()

    def put_and_save(self, key: str, value: Any):
        self.put(key, value)
        self.save()

    def value_of(self, key: str) -> Any:
        return self._data.get(key, None)

    def instance_value_of(self, key: str, cls: type, default=None) -> Any:
        v = self.value_of(key)
        if isinstance(v, cls):
            return v
        return default

    def str_of(self, key: str, default=None) -> str:
        return self.instance_value_of(key, str, default=default)

    def int_of(self, key: str, default=None) -> int:
        return self.instance_value_of(key, int, default=default)

    def float_of(self, key: str, default=None) -> float:
        return self.instance_value_of(key, float, default=default)

    def list_of(self, key: str, default=None) -> list:
        return self.instance_value_of(key, list, default=default)

    def dict_of(self, key: str, default=None) -> dict:
        return self.instance_value_of(key, dict, default=default)


uconfig = UiConfig(_ui_config_file)

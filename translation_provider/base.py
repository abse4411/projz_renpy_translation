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
from typing import List, Tuple

from config.base import default_config

_API_PROVIDERS = {}


class ApiTranslator:

    def translate(self, text: str) -> str:
        return NotImplementedError()

    def translate_batch(self, texts: List[str]) -> List[str]:
        return [self.translate(t) for t in texts]

    def close(self):
        '''
        Release resources if necessary
        :return:
        '''
        pass


class Provider:
    def __init__(self):
        self.config = default_config

    def default_api(self) -> str:
        """
        return the default API name from the config file
        :return:
        """
        return None

    def default_source_lang(self) -> str:
        """
        return the default source language from the config file
        :return:
        """
        return None

    def default_target_lang(self) -> str:
        """
        return the default target language from the config file
        :return:
        """
        return None

    def api_names(self) -> List[str]:
        """
        return supported APIs
        :return: a list of APIs
        """
        return []

    def languages_of(self, api: str) -> Tuple[List[str], List[str]]:
        """
        return supported languages of this api
        :param api:
        :return: a tuple of (supported source languages, supported target languages)
        """
        return [], []

    def translator_of(self, api: str, source_lang: str, target_lang: str) -> ApiTranslator:
        raise NotImplementedError()


def registered_providers():
    return list(_API_PROVIDERS.keys())


def register_provider(provider_name: str, translator: Provider):
    assert provider_name not in _API_PROVIDERS
    _API_PROVIDERS[provider_name] = translator


def unregister_provider(provider_name: str):
    return _API_PROVIDERS.pop(provider_name, None)


def get_provider(provider_name: str) -> Provider:
    return _API_PROVIDERS.get(provider_name, None)

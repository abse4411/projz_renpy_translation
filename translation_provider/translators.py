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
from typing import List

from trans import Translator
from trans.translators_api import TranslatorsTranslator
from translation_provider.base import Provider, register_provider

import translators as ts

from util.translate import BatchTranslator


class TranslatorsApi(Provider):

    def __init__(self):
        super().__init__()
        self.trans_kwargs = None
        self.tconfig = None
        self.reload_config()

    def reload_config(self):
        self.tconfig = self.config['translator']['translators']
        self.trans_kwargs = self.tconfig.get('translate_text', {})

    def api_names(self):
        return list(ts.translators_pool)

    def default_api(self):
        self.reload_config()
        return self.tconfig.get('api_name', 'bing')

    def default_source_lang(self):
        self.reload_config()
        return self.tconfig.get('from_language', 'auto')

    def default_target_lang(self):
        self.reload_config()
        return self.tconfig['to_language']

    def languages_of(self, api: str):
        langs = sorted(list(ts.get_languages(api).keys()))
        return ['auto'] + langs, langs

    def translator_of(self, api: str, source_lang: str, target_lang: str) -> Translator:
        if api in self.api_names():
            s, t = self.languages_of(api)
            if source_lang in s and target_lang in t:
                _separator = self.tconfig['batch_separator']
                _max_len = self.tconfig['batch_max_textlen']
                _batch_size = self.tconfig['batch_size']
                return BatchTranslator(TranslatorsTranslator(api, source_lang, target_lang, self.trans_kwargs),
                                       _separator, _max_len, _batch_size)
        return None


register_provider('translators', TranslatorsApi())

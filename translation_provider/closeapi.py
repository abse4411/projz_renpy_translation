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
from openai_api import OpenAITranslator
from store.misc import strip_tags
from trans import Translator
from translation_provider.base import Provider, register_provider
from util import strip_or_none


class _InnerTranslator(Translator):
    def __init__(self, api: str, from_lang: str, to_lang: str):
        self._api = api
        self._source = from_lang
        self._target = to_lang
        self._open_ai = OpenAITranslator(target_lang=self._target, model=self._api)

    def translate(self, text: str):
        stripped_text = strip_or_none(strip_tags(text))
        if stripped_text is not None:
            return self._open_ai.translate(stripped_text)
        return text

    def close(self):
        self._open_ai.close()


class TranslatorsApi(Provider):

    def __init__(self):
        super().__init__()
        self.oconfig = self.config['translator']['open_ai']
        self.slangs = ['Auto']

    def api_names(self):
        return self.oconfig['models']

    def default_api(self):
        return self.oconfig['chat']['completions']['model']

    def default_source_lang(self):
        return self.slangs[0]

    def default_target_lang(self):
        return self.oconfig['target_lang']

    def languages_of(self, api: str):
        return self.slangs, self.oconfig['langs']

    def translator_of(self, api: str, source_lang: str, target_lang: str) -> Translator:
        return _InnerTranslator(api, source_lang, target_lang)


register_provider('CloseAI', TranslatorsApi())

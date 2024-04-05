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
from translation_provider.base import Provider, register_provider

_preacceleration_done = False
ts = None


class _InnerTranslator(Translator):
    def __init__(self, api: str, from_lang: str, to_lang: str, trans_kwargs):
        self._api = api
        self._source = from_lang
        self._target = to_lang
        self._trans_kwargs = trans_kwargs

    def translate(self, text: str):
        return ts.translate_text(text, from_language=self._source, to_language=self._target,
                                 translator=self._api, **self._trans_kwargs)


class TranslatorsApi(Provider):

    def __init__(self):
        super().__init__()
        self.trans_kwargs = None
        self.tconfig = None
        self.reload_config()

    def reload_config(self):
        self.tconfig = self.config['translator']['translators']
        self.trans_kwargs = self.tconfig.get('translate_text', {})
        self.trans_kwargs.pop('query_text', None)
        self.trans_kwargs.pop('translator', None)
        self.trans_kwargs.pop('from_language', None)
        self.trans_kwargs.pop('to_language', None)

    def api_names(self):
        global ts
        import translators as ts
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
        global ts
        import translators as ts
        langs = sorted(list(ts.get_languages(api).keys()))
        return ['auto']+langs, langs

    def translator_of(self, api: str, source_lang: str, target_lang: str) -> Translator:
        global ts
        import translators as ts
        use_preacceleration = self.trans_kwargs.pop('if_use_preacceleration', False)
        global _preacceleration_done
        if use_preacceleration and not _preacceleration_done:
            kwargs = self.tconfig.get('preaccelerate', {})
            from translators.server import preaccelerate
            _ = preaccelerate(kwargs)
            _preacceleration_done = True
        if api in self.api_names():
            s, t = self.languages_of(api)
            if source_lang in s and target_lang in t:
                return _InnerTranslator(api, source_lang, target_lang, self.trans_kwargs)
        return None


register_provider('translators', TranslatorsApi())

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
import time

from config import default_config
from trans import Translator

import translators as ts

_preacceleration_done = False


def _preaccelerate(**preacc_kwargs):
    global _preacceleration_done
    if _preacceleration_done:
        return
    else:
        _preacceleration_done = True
        from translators.server import preaccelerate
        _ = preaccelerate(preacc_kwargs)


class TranslatorsTranslator(Translator):

    def __init__(self, api: str, source: str, target: str, verbose: bool = True):
        '''

        :param api: The "translator" arg for ts.translate_text
        :param source: The "from_language" arg for ts.translate_text
        :param target: The "to_language" arg for ts.translate_text
        :param verbose: Print translation info
        '''

        self._verbose = verbose
        self._api = api
        self._source = source
        self._target = target
        tconfig = default_config['translator']['translators']
        self.trans_kwargs = tconfig.get('translate_text', {})
        use_preacceleration = self.trans_kwargs.pop('if_use_preacceleration', True)
        if use_preacceleration and not _preacceleration_done:
            preacc_kwargs = tconfig.get('preaccelerate', {})
            _preaccelerate(**preacc_kwargs)
        self.trans_kwargs.pop('query_text', None)
        self.trans_kwargs.pop('translator', None)
        self.trans_kwargs.pop('from_language', None)
        self.trans_kwargs.pop('to_language', None)

    def translate(self, text: str) -> str:
        st_time = time.time()
        res = ts.translate_text(text, from_language=self._source, to_language=self._target,
                                translator=self._api, **self.trans_kwargs)
        if self._verbose:
            print(f'[Elapsed: {time.time() - st_time:.1f}s]: {text}->{res}')
        return res

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
from collections import defaultdict
from typing import List, Tuple, Union, Any

from store.unit import TranslationItem


class TranslationDict:
    def __init__(self):
        self.lang_dict = defaultdict(dict)

    def __getitem__(self, key: Union[str, List, Tuple]):
        if isinstance(key, str):
            lang = key
            if lang in self.lang_dict:
                return self.lang_dict[lang]
            return None
        elif isinstance(key, (tuple, list)) and len(key) == 2:
            lang, tid = key
            if lang in self.lang_dict:
                lang_data = self.lang_dict[lang]
                if tid in lang_data:
                    return lang_data[tid]
            return None
        else:
            raise RuntimeError('key should a string, or a list or tuple with size=2')

    def safe_add_key(self, key: str, value: dict = None):
        assert isinstance(key, str), 'key should a str'
        if value is not None:
            assert isinstance(key, dict), 'value should a dict'
        else:
            value = dict()
        if key not in self.lang_dict:
            self.lang_dict[key] = value

    def __setitem__(self, key: Union[List, Tuple], value: Any):
        assert isinstance(key, (tuple, list)) and len(key) == 2, 'key should a list or tuple with size=2'
        lang, tid = key
        self.lang_dict[lang][tid] = value

    def __contains__(self, key: Union[str, List, Tuple]):
        return self[key] is not None

    def len(self, key: str = None):
        if isinstance(key, str):
            lang = key
            return len(self.lang_dict[lang])
        else:
            return sum([len(d) for d in self.lang_dict.values()])

    def langs(self):
        return self.lang_dict.keys()

    def items(self):
        return self.lang_dict.items()

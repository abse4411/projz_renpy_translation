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
import argparse

from config import default_config
from store import TranslationIndex


class BaseCmd:
    def __init__(self, name: str, description: str):
        self._parser = argparse.ArgumentParser(prog=name, description=description)
        self.name = name
        self.description = description
        self.config = default_config
        self.args = None

    def parse_args(self, text: str):
        self.args = self._parser.parse_args(text.split())

    def invoke(self):
        pass


class BaseIndexCmd(BaseCmd):
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self._parser.add_argument("index_or_name", help="The index or nickname of TranslationIndex to select.")
        self._index = None
        self._nick_name = None

    @staticmethod
    def parse_index_or_name(index_or_name: str):
        index = None
        try:
            index = int(index_or_name)
        except:
            pass
        nick_name = index_or_name
        return index, nick_name

    def parse_args(self, text: str):
        super().parse_args(text)
        self._index, self._nick_name = self.parse_index_or_name(self.args.index_or_name)

    def get_translation_index(self):
        res = TranslationIndex.from_docid_or_nickname(self._index, self._nick_name)
        assert res is not None, \
            'Could\'n load this TranslationIndex. Please check whether the entered index or nickname is correct'
        return res


class BaseLangIndexCmd(BaseIndexCmd):
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self._parser.add_argument("-l", "--lang", required=True, type=str, metavar='language',
                                  help="The language to use.")


class BaseConfirmationCmd(BaseCmd):
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self._parser.add_argument("-y", "--yes", action='store_true', help="Assume yes to all queries.")


class BaseIndexConfirmationCmd(BaseIndexCmd):
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self._parser.add_argument("-y", "--yes", action='store_true', help="Assume yes to all queries.")


class BaseLangIndexConfirmationCmd(BaseLangIndexCmd):
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self._parser.add_argument("-y", "--yes", action='store_true', help="Assume yes to all queries.")

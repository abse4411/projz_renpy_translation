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
import json
from typing import List


class BlockItem:
    def __init__(self, type=None, what=None, who=None, code=None, new_code=None):
        self.type = type
        self.what = what
        self.who = who
        self.code = code
        self.new_code = new_code

    @property
    def is_say(self):
        return 'Say' in self.type

    def to_dict(self):
        return {
            'type': self.type,
            'what': self.what,
            'who': self.who,
            'code': self.code,
            'new_code': self.new_code,
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, obj_dict: dict):
        return cls(
            type=obj_dict.get('type', None),
            what=obj_dict.get('what', None),
            who=obj_dict.get('who', None),
            code=obj_dict.get('code', None),
            new_code=obj_dict.get('new_code', None),
        )


class TranslationItem:
    def __init__(self, identifier=None, language=None, filename=None, linenumber=None, block: List[BlockItem] = None):
        self.identifier = identifier,
        self.language = language,
        self.filename = filename,
        self.linenumber = linenumber,
        self.block = block if block is not None else []

    def to_dict(self):
        return {
            'identifier': self.identifier,
            'language': self.language,
            'filename': self.filename,
            'linenumber': self.linenumber,
            'block': [b.to_dict() for b in self.block],
        }

    def __repr__(self):
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, obj_dict: dict):
        blocks = []
        for b in obj_dict['block']:
            blocks.append(BlockItem.from_dict(b))
        return cls(
            identifier=obj_dict.get('identifier', None),
            language=obj_dict.get('language', None),
            filename=obj_dict.get('filename', None),
            linenumber=obj_dict.get('linenumber', None),
            block=blocks
        )

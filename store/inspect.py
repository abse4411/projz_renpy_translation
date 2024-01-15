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

from store import TranslationIndex
from util import to_translatable_text
from util.renpy import list_vars, list_tags, list_escape_chars

PRESENT_FIELDS = ['tid', 'new_text', 'raw_text', 'message', 'filename', 'linenumber', 'identifier']


def detect_missing_vars_and_tags(index: TranslationIndex, lang: str, say_only=True):
    error_translations = []
    if lang is None:
        return error_translations

    dialogue_data, string_data = index._list_translations(lang)

    def _detect(old_text: str, new_text: str):
        msg = ''
        o_vars = list_vars(old_text)
        n_vars = list_vars(new_text)
        for k, cnt in o_vars.items():
            if k not in n_vars or n_vars[k] != cnt:
                msg += f'Miss variable: {k}. Expected occurrence times:{cnt}, got:{n_vars.get(k, 0)}.\n'

        o_tags = list_tags(old_text)
        n_tags = list_tags(new_text)
        for k, cnt in o_tags.items():
            if k not in n_tags or n_tags[k] != cnt:
                msg += f'Miss tag: {k}. Expected occurrence times:{cnt}, got:{n_tags.get(k, 0)}.\n'

        o_ecahrs = list_escape_chars(old_text)
        n_ecahrs = list_escape_chars(new_text)
        for k, cnt in o_ecahrs.items():
            if k not in n_ecahrs or n_ecahrs[k] != cnt:
                msg += f'Miss escape character: {k}. Expected occurrence times:{cnt}, got:{n_ecahrs.get(k, 0)}.\n'
        return msg

    for v in dialogue_data:
        for i, b in enumerate(v['block']):
            if TranslationIndex._is_say_block(b):
                old_str, new_str = to_translatable_text(b['what']), to_translatable_text(b['new_code'])
            else:
                if not say_only:
                    old_str, new_str = b['code'], b['new_code']
                else:
                    continue
            if old_str is not None and new_str is not None:
                message = _detect(old_str, new_str)
                if message != '':
                    error_translations.append({
                        'tid': TranslationIndex._encode_tid(index.DIALOGUE_ID_PREFIX, i, v.doc_id),
                        'message': message,
                        'raw_text': old_str,
                        'new_text': new_str,
                        'identifier': v['identifier'],
                        'filename': v['filename'],
                        'linenumber': v['linenumber'],
                    })
    for v in string_data:
        for i, b in enumerate(v['block']):
            old_str, new_str = to_translatable_text(b['what']), to_translatable_text(b['new_code'])
            if old_str is not None and new_str is not None:
                message = _detect(old_str, new_str)
                if message != '':
                    error_translations.append({
                        'tid': TranslationIndex._encode_tid(index.STRING_ID_PREFIX, i, v.doc_id),
                        'message': message,
                        'raw_text': old_str,
                        'new_text': new_str,
                        'identifier': v['identifier'],
                        'filename': v['filename'],
                        'linenumber': v['linenumber'],
                    })

    return error_translations

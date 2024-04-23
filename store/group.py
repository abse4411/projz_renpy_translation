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
from util import assert_not_blank, to_translatable_text

ALL = 'all'
TRANS = 'translated'
UNTRANS = 'untranslated'
_SCOPES = [ALL, TRANS, UNTRANS]
ALL_FIELDS = ['tid', 'new_text', 'old_text', 'language', 'filename', 'linenumber', 'identifier']
GROUPBY_FIELDS = ['filename']
SORTBY_FIELDS = ['tid', 'linenumber', 'identifier']


def group_translations_by(field_name: str, sorted_by: str, scope: str, index: TranslationIndex, lang: str,
                          reverse=False, say_only=True):
    group_map = defaultdict(list)
    field_name = assert_not_blank(field_name)
    if sorted_by is not None:
        sorted_by = assert_not_blank(sorted_by)
    if lang is None:
        return group_map

    select_func = None
    if scope == ALL:
        def select_func(x):
            return True
    elif scope == TRANS:
        def select_func(x):
            return x['new_code'] is not None
    elif scope == UNTRANS:
        def select_func(x):
            return x['new_code'] is None
    else:
        f'Expect one of {_SCOPES}, but got:{scope}'

    def _merge(vi: dict, bi: dict):
        res = bi.copy()
        res.update(vi)
        if res['filename'].startswith('renpy/common'):
            res['filename'] = 'common.rpy'
        if TranslationIndex._is_say_block(b) or res['what'] is not None:
            res['old_text'] = to_translatable_text(res['what'])
            res['new_text'] = to_translatable_text(res['new_code'])
        else:
            res['old_text'] = res['code']
            res['new_text'] = res['new_code']
        # we pop items that may confuse the user
        res.pop('block')
        res.pop('new_code')
        res.pop('who')
        res.pop('what')
        res.pop('type')
        return res

    dialogue_data, string_data = index._list_translations(lang)
    for v in dialogue_data:
        for i, b in enumerate(v['block']):
            new_item = _merge(v, b)
            if select_func(b):
                if TranslationIndex._is_say_block(b) or not say_only:
                    new_item['tid'] = TranslationIndex._encode_tid(index.DIALOGUE_ID_PREFIX, i, v.doc_id)
                    group_map[new_item[field_name]].append(new_item)
    for v in string_data:
        for i, b in enumerate(v['block']):
            new_item = _merge(v, b)
            if select_func(b):
                new_item['tid'] = TranslationIndex._encode_tid(index.STRING_ID_PREFIX, i, v.doc_id)
                new_item['old_text'] = to_translatable_text(b['what'])
                group_map[new_item[field_name]].append(new_item)

    if sorted_by:
        for k in group_map.keys():
            group_map[k] = sorted(group_map[k], key=lambda x: x[sorted_by], reverse=reverse)

    return group_map

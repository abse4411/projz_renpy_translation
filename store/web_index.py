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
import os.path
import random
import uuid

from config import default_config
from injection import Project
from store import TranslationIndex, index_type
from store.database.base import db_context
from store.index import extra_data_of
from store.index_type import register_index
from store.misc import ast_of, block_of, strip_tags, quote_with_fonttag
from util import exists_file, assert_not_blank, default_read, default_write


class WebTranslationIndex(TranslationIndex):

    def __init__(self, project: Project, nickname: str, tag: str, stats: dict = None, db_file: str = None,
                 extra_data: dict = None, doc_id: int = None):
        extra_data = extra_data_of(index_type.WEB, extra_data)
        super().__init__(project, nickname, tag, stats, db_file, extra_data, doc_id)
        self._font_dir = default_config['renpy']['font']['save_dir']
        self._font = extra_data['font']

    @property
    def project_version(self):
        return f'{super().project_version}[WEB]'

    @classmethod
    def _load_from_json(cls, data: dict):
        strings = data.get('String', {})
        dialogues = data.get('Say', {})
        dialogue_data, string_data = [], []

        def _collect(item, t):
            lang = item['language']
            if lang is None:
                lang = 'None'
            identifier = item['identifier']
            substituted = strip_tags(item['substituted'])
            what = item['text']
            who = item.get('who', None)
            filename = item.get('filename', 'projz_translations.rpy')
            linenumber = item.get('linenumber', 0)
            code = item.get('code', None)
            return ast_of(language=lang, filename=filename, linenumber=linenumber, identifier=identifier,
                          block=[block_of(type=t, what=what, who=who, code=code, new_code=substituted)])

        for d in dialogues.values():
            dialogue_data.append(_collect(d, 'Say'))
        for s in strings.values():
            string_data.append(_collect(s, 'String'))
        return dialogue_data, string_data

    @classmethod
    def from_index(cls, index: TranslationIndex):
        if index.itype == index_type.WEB:
            res = cls(index.project, index.nickname, index.tag, index._stats, index._db_file, index._extra_data,
                      index.doc_id)
            return res
        else:
            raise ValueError(f'Unable to cast {index.to_dict()} into a WebTranslationIndex')

    @classmethod
    def from_data(cls, p: Project, data: dict, nickname: str, tag: str, font: str, lang: str):
        nickname, tag = cls._process_name(nickname, tag)
        nickname, tag = cls.check_existing_with(nickname, tag)
        lang = assert_not_blank(lang, 'lang')
        res = cls(p, nickname, tag, extra_data={'font': font})
        res.save()
        dialogue_data, string_data = cls._load_from_json(data)
        with res._open_db() as dao:
            res.drop_translations(lang)
            dlang, slang = res._get_table_name(lang)
            dao.add_batch(dlang, dialogue_data)
            dao.add_batch(slang, string_data)
            # update statistics when updating translation
            res.update_translation_stats(lang, say_only=True)
        res.save()
        return res

    @db_context
    def import_translations(self, lang: str, translated_only: bool = True, say_only: bool = True):
        lang = assert_not_blank(lang, 'lang')
        json_file = os.path.join(self.project_path, 'projz_translations.json')
        if exists_file(json_file):
            with default_read(json_file) as f:
                data = json.load(f)
        dialogue_data, string_data = self._load_from_json(data)
        if dialogue_data or string_data:
            with self._open_db() as dao:
                self.drop_translations(lang)
                dlang, slang = self._get_table_name(lang)
                dao.add_batch(dlang, dialogue_data)
                dao.add_batch(slang, string_data)
                # update statistics when updating translation
                self.update_translation_stats(lang, say_only=say_only)
        else:
            print(f'Empty translations of language {lang}')
        print(f'{lang}: {len(dialogue_data)} dialogue translations and {len(string_data)} string translations found')

    def _quote_with_fonttag(self, text):
        return quote_with_fonttag(self._font_dir, self._font, text)

    @db_context
    def export_translations(self, lang: str, translated_only: bool = True, say_only: bool = True):
        lang = assert_not_blank(lang, 'lang')
        if not self.exists_lang(lang):
            print(f'No {lang} translations to export')
            return
        dialogue_data, string_data = self._list_translations(lang)
        new_string_data, new_dialogue_data = {}, {}
        for v in dialogue_data:
            b = v['block'][0]
            tid = v['identifier']
            if b['new_code'] is not None:
                b['new_code'] = self._quote_with_fonttag(b['new_code'])
            elif not translated_only:
                b['new_text'] = self._quote_with_fonttag(b['substituted'])
            new_dialogue_data[tid] = b
        for v in string_data:
            b = v['block'][0]
            tid = v['identifier']
            if b['new_code'] is not None:
                b['new_code'] = self._quote_with_fonttag(b['new_code'])
            elif not translated_only:
                b['new_text'] = self._quote_with_fonttag(b['substituted'])
            new_string_data[tid] = b
        if len(new_dialogue_data) == 0 and len(new_string_data) == 0:
            print(f'No {lang} translations in this TranslationIndex to export')
            return
        print(f'{lang}: {len(new_dialogue_data)} dialogue and {len(new_string_data)} string translations '
              f'are ready to export')
        dmap, smap = {}, {}
        json_file = os.path.join(self.project_path, 'projz_translations.json')
        if exists_file(json_file):
            with default_read(json_file) as f:
                data = json.load(f)
            dmap = data.get('Say', {})
            smap = data.get('String', {})
        dmap.update(new_dialogue_data)
        smap.update(new_string_data)
        with default_write(json_file) as f:
            json.dump({'String': smap, 'Say': dmap}, f, ensure_ascii=False, indent=2)
        print(f'We have written translations to: {json_file}')

    def count_translations(self, lang: str, show_detail: bool = False, say_only: bool = True):
        raise NotImplementedError()


register_index(WebTranslationIndex.from_index, index_type.WEB)

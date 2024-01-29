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
import glob
import os.path
import random
import uuid
from collections import defaultdict
from typing import Tuple, List

import regex

from config import default_config
from injection import Project, get_translations, generate_translations, count_translations
from store.database import TranslationIndexDao, TranslationDao
from store.database.base import db_context
from util import exists_dir, strip_or_none, assert_not_blank, strip_linebreakers, exists_file, to_translatable_text, \
    to_string_text
from util.renpy import list_tags


def encode_sumid(index: int, n_len: int):
    s1 = hex(index)[2:]
    s2 = hex(n_len)[2:]
    s3 = hex(index + n_len - len(s2))[-len(s2):]
    s1 = '0' * (len(s2) - len(s1)) + s1
    return s1 + s2 + s3


def decode_sumid(id_str: str):
    if id_str:
        id_str = id_str.strip()
        if id_str == '' or len(id_str) % 3 != 0:
            return None, None
    s_len = len(id_str) // 3
    try:
        index = int(id_str[:s_len], 16)
        n_len = int(id_str[s_len:-s_len], 16)
        s3 = id_str[-s_len:]
        if hex(index + n_len - s_len)[-s_len:] == s3:
            return index, n_len
    except:
        pass
    return None, None


def _get_task_result(res):
    return res['items'], res['message']


class TranslationIndex:
    DIALOGUE_ID_PREFIX = 'D'
    STRING_ID_PREFIX = 'S'
    TID_PATTERN = regex.compile(r'^([DS])(\d+)_(\d+)$')

    def __init__(self, project: Project, nickname: str, tag: str, stats: dict = None, db_file: str = None):
        self._doc_id = None
        self._project = project
        self._nickname = nickname
        self._tag = tag
        self._stats = stats if stats is not None else {'dialogue': dict(), 'string': dict()}
        self._db_file = os.path.join(default_config.project_path,
                                     f'projz_{self._nickname}_{self._tag}.db') if db_file is None else db_file

    @property
    def doc_id(self):
        return self._doc_id

    @property
    def project(self):
        return self._project

    @property
    def nickname(self):
        return self._nickname

    @property
    def tag(self):
        return self._tag

    @property
    def project_path(self):
        return self._project.project_path

    @property
    def project_name(self):
        return self._project.game_info.get('game_name', None)

    @property
    def project_version(self):
        return self._project.game_info.get('game_version', None)

    @property
    def project_renpy_version(self):
        return self._project.game_info.get('renpy_version', None)

    @property
    def game_info(self):
        return self._project.game_info.copy()

    @property
    def injection_state(self):
        return self._project.injection_state.copy()

    @property
    def translation_state(self):
        return self._stats.copy()

    @staticmethod
    def _encode_tid(prefix: str, block_idx: int, doc_id: str):
        return f'{prefix}{block_idx}_{doc_id}'

    @staticmethod
    def _decode_tid(tid: str):
        if tid is not None:
            match = TranslationIndex.TID_PATTERN.match(tid)
            if match:
                p, block_idx, doc_id = match.groups()
                return p, int(block_idx), int(doc_id)
        return None, None, None

    @staticmethod
    def is_valid_tid(tid: str):
        res = TranslationIndex._decode_tid(tid)
        return res[0] is not None

    @staticmethod
    def _is_say_block(data):
        return 'Say' in data.get('type', '')

    @staticmethod
    def _is_user_block(data):
        return 'UserStatement' in data.get('type', '')

    @staticmethod
    def _get_userblock_text(block):
        arr = block.get('parsed', None)
        if arr:
            for i, text in enumerate(arr):
                if len(text) > 1 and ((text[0] == '"' and text[-1] == '"') or
                                      (text[0] == '\'' and text[-1] == '\'')):
                    return i, text[1:-1]
        return -1, None

    @staticmethod
    def _to_userblock_text(block, new_text):
        idx, res = TranslationIndex._get_userblock_text(block)
        if res:
            arr = block['parsed']
            if res is not None:
                return block['code'].replace(arr[idx], f'"{new_text}"', 1)
        return None

    @staticmethod
    def _get_table_name(lang: str):
        return TranslationIndex.DIALOGUE_ID_PREFIX + lang, TranslationIndex.STRING_ID_PREFIX + lang

    def _open_db(self):
        return TranslationDao(self._db_file)

    @db_context
    def update_translation_stats(self, lang: str = None, say_only=True):
        dialogue_stats = dict()
        strings_stats = dict()

        def count_dialogue(ddata):
            trans_cnt, untrans_cnt = 0, 0
            for v in ddata:
                for i, b in enumerate(v['block']):
                    if not self._is_say_block(b) and say_only:
                        continue
                    if b['new_code'] is not None:
                        trans_cnt += 1
                    else:
                        untrans_cnt += 1
            return trans_cnt, untrans_cnt

        def count_string(sdata):
            trans_cnt, untrans_cnt = 0, 0
            for v in sdata:
                for i, b in enumerate(v['block']):
                    if b['new_code'] is not None:
                        trans_cnt += 1
                    else:
                        untrans_cnt += 1
            return trans_cnt, untrans_cnt

        with self._open_db() as dao:
            lang = strip_or_none(lang)
            if lang is not None:
                if self.exists_lang(lang):
                    dialogue_stats = self._stats['dialogue']
                    strings_stats = self._stats['string']
                    langs = self._get_table_name(lang)
                else:
                    print(f'The language {lang} is not found!')
                    return
            else:
                langs = dao.list_langs()
            for lang in langs:
                if lang.startswith(self.DIALOGUE_ID_PREFIX):
                    dialogue_stats[lang[len(self.DIALOGUE_ID_PREFIX):]] = count_dialogue(dao.list_by_lang(lang))
                elif lang.startswith(self.STRING_ID_PREFIX):
                    strings_stats[lang[len(self.STRING_ID_PREFIX):]] = count_string(dao.list_by_lang(lang))
                else:
                    # who saves the undefined lang?
                    pass
        new_stats = {
            'dialogue': dialogue_stats,
            'string': strings_stats,
        }
        self._update({'stats': new_stats})

    def exists_lang(self, lang):
        lang = strip_or_none(lang)
        if lang is not None:
            with self._open_db() as dao:
                langs = dao.list_langs()
                dlang, slang = self._get_table_name(lang)
                if dlang in langs or slang in langs:
                    return True
        return False

    def drop_translations(self, lang: str):
        lang = strip_or_none(lang)
        if lang is None:
            return
        dlang, slang = self._get_table_name(lang)
        with self._open_db() as dao:
            dao.delete_by_lang(dlang)
            dao.delete_by_lang(slang)
            # update translation stats
            if lang in self._stats['dialogue']:
                self._stats['dialogue'].pop(lang)
            if lang in self._stats['string']:
                self._stats['string'].pop(lang)
            self._update({'stats': self._stats})

    def _list_translations(self, lang: str):
        lang = strip_or_none(lang)
        if lang is None:
            return [], []
        with self._open_db() as dao:
            langs = dao.list_langs()
            dlang, slang = self._get_table_name(lang)
            if dlang not in langs and slang not in langs:
                return [], []
            dialogue_data = dao.list_by_lang(dlang)
            string_data = dao.list_by_lang(slang)
        return dialogue_data, string_data

    def get_translated_lines(self, lang: str, say_only=True, source_code=False, not_modify: bool = False):
        res = []
        lang = strip_or_none(lang)
        if lang is None:
            return res
        dialogue_data, string_data = self._list_translations(lang)
        if len(dialogue_data) == 0 and len(string_data) == 0:
            print(f'No translated lines of language {lang}')
            return res

        strip_tag = default_config['index']['strip_tag']

        if not_modify:
            def _strip_fn(text):
                return text
        else:
            def _strip_fn(text):
                if strip_tag and text:
                    tags = list_tags(text)
                    for tag, _ in tags.items():
                        text = text.replace(tag, '')
                return text

        for v in dialogue_data:
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    if self._is_say_block(b):
                        res.append([self._encode_tid(self.DIALOGUE_ID_PREFIX, i, v.doc_id),
                                    _strip_fn(to_translatable_text(b['new_code']))])
                    else:
                        if not say_only:
                            if source_code:
                                old_text = b['code']
                            else:
                                _, old_text = self._get_userblock_text(b)
                            if old_text is None:
                                continue
                            res.append([self._encode_tid(self.DIALOGUE_ID_PREFIX, i, v.doc_id),
                                        _strip_fn(to_translatable_text(old_text))])
        for v in string_data:
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    res.append([self._encode_tid(self.STRING_ID_PREFIX, i, v.doc_id),
                                _strip_fn(to_translatable_text(b['new_code']))])
        return res

    @db_context
    def rename_lang(self, lang: str, target_name: str):
        lang = assert_not_blank(lang, 'lang')
        new_lang = assert_not_blank(target_name, 'target_name')
        if not self.exists_lang(lang):
            print(f'The language {lang} is not found!')
            return
        if self.exists_lang(new_lang):
            print(f'The language {target_name} already exists!')
            return
        dialogue_data, string_data = self._list_translations(lang)
        for v in dialogue_data:
            v['language'] = new_lang
        for v in string_data:
            v['language'] = new_lang
        dlang, slang = self._get_table_name(lang)
        tdlang, tslang = self._get_table_name(target_name)
        with self._open_db() as dao:
            dao.delete_by_lang(tdlang)
            dao.delete_by_lang(tslang)
            dao.add_batch(tdlang, dialogue_data)
            dao.add_batch(tslang, string_data)
            dao.delete_by_lang(dlang)
            dao.delete_by_lang(slang)
            # update translation stats
            if lang in self._stats['dialogue']:
                old_stats = self._stats['dialogue'].pop(lang)
                self._stats['dialogue'][target_name] = old_stats
            if lang in self._stats['string']:
                old_stats = self._stats['string'].pop(lang)
                self._stats['string'][target_name] = old_stats
            self._update({'stats': self._stats})

    def get_untranslated_lines(self, lang: str, say_only=True, source_code=False, not_modify: bool = False):
        res = []
        lang = strip_or_none(lang)
        if lang is None:
            return res
        dialogue_data, string_data = self._list_translations(lang)
        if len(dialogue_data) == 0 and len(string_data) == 0:
            print(f'No untranslated lines of language {lang}')
            return res

        strip_tag = default_config['index']['strip_tag']

        if not_modify:
            def _strip_fn(text):
                return text
        else:
            def _strip_fn(text):
                if strip_tag and text:
                    tags = list_tags(text)
                    for tag, _ in tags.items():
                        text = text.replace(tag, '')
                return text

        for v in dialogue_data:
            for i, b in enumerate(v['block']):
                if b['new_code'] is None:
                    if self._is_say_block(b):
                        res.append([self._encode_tid(self.DIALOGUE_ID_PREFIX, i, v.doc_id),
                                    _strip_fn(to_translatable_text(b['what']))])
                    else:
                        if not say_only:
                            if source_code:
                                old_text = b['code']
                            else:
                                _, old_text = self._get_userblock_text(b)
                            if old_text is None:
                                continue
                            res.append([self._encode_tid(self.DIALOGUE_ID_PREFIX, i, v.doc_id),
                                        _strip_fn(to_translatable_text(old_text))])
        for v in string_data:
            for i, b in enumerate(v['block']):
                if b['new_code'] is None:
                    res.append([self._encode_tid(self.STRING_ID_PREFIX, i, v.doc_id),
                                _strip_fn(to_translatable_text(b['what']))])
        return res

    @db_context
    def clear_untranslated_lines(self, lang: str, say_only=True):
        lang = strip_or_none(lang)
        if lang is None:
            return
        dialogue_data, string_data = self._list_translations(lang)
        if len(dialogue_data) == 0 and len(string_data) == 0:
            print(f'No untranslated lines of language {lang}')
            return

        # get all untranslations first, mapped by tid
        ddocid_map = dict()
        sdocid_map = dict()
        updated_ddocids = set()
        updated_sdocids = set()
        for v in dialogue_data:
            ddocid_map[v.doc_id] = v['block']
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    continue
                if not self._is_say_block(b) and say_only:
                    continue
                if self._is_say_block(b):
                    b['new_code'] = b['what']
                else:
                    b['new_code'] = b['code']
                updated_ddocids.add(v.doc_id)
        for v in string_data:
            sdocid_map[v.doc_id] = v['block']
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    continue
                b['new_code'] = b['what']
                updated_sdocids.add(v.doc_id)

        if len(updated_ddocids) == 0 and len(updated_sdocids) == 0:
            print(f'No untranslated lines of language {lang} to be updated')
            return

        # write updated translations to db
        dlang, slang = self._get_table_name(lang)
        self._update_batch(dlang, updated_ddocids, ddocid_map)
        self._update_batch(slang, updated_sdocids, sdocid_map)
        # update statistics when updating translation
        self.update_translation_stats(lang, say_only=say_only)
        print(f'{lang}: {len(updated_ddocids)} updated dialogue translations, '
              f'{len(updated_sdocids)} updated string translations.')

    @db_context
    def merge_translations_from(self, target_index: 'TranslationIndex', lang: str, say_only=True):
        assert target_index is not None, f'target_index must not be None'
        assert target_index != self, 'Cannot merge from self'
        lang = assert_not_blank(lang, 'lang')
        if not self.exists_lang(lang):
            print(f'No translations of language {lang} in target TranslationIndex, please import it first')
            return
        if not target_index.exists_lang(lang):
            print(f'No translations of language {lang} in source TranslationIndex, please import it first')
            return
        dialogue_data, string_data = self._list_translations(lang)

        # get all untranslations first, mapped by identifier
        id_dblock_map = dict()
        id_sblock_map = dict()
        ddocid_map = dict()
        sdocid_map = dict()
        for v in dialogue_data:
            ddocid_map[v.doc_id] = v['block']
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    continue
                if not self._is_say_block(b) and say_only:
                    continue
                id_dblock_map[(v['identifier'], i)] = (b, v.doc_id)
        for v in string_data:
            sdocid_map[v.doc_id] = v['block']
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    continue
                id_sblock_map[(v['identifier'], i)] = (b, v.doc_id)

        if len(id_dblock_map) == 0 and len(id_sblock_map) == 0:
            print(f'No translations of language {lang} to be merged')
            return
        # record updated doc_id
        updated_ddocids = set()
        updated_sdocids = set()
        use_cnt = 0
        find_cnt = 0

        def _update_dialogue(identifier, block_i, new_code, block_type):
            nonlocal use_cnt
            block, doc_id = id_dblock_map.get((identifier, block_i), (None, None))
            if block and block_type == block['type']:
                block['new_code'] = new_code
                updated_ddocids.add(doc_id)
                use_cnt += 1

        def _update_string(identifier, block_i, new_code):
            nonlocal use_cnt
            block, doc_id = id_sblock_map.get((identifier, block_i), (None, None))
            if block:
                block['new_code'] = new_code
                updated_sdocids.add(doc_id)
                use_cnt += 1

        # for each translation in source index
        source_dialogue_data, source_string_data = target_index._list_translations(lang)
        for v in source_dialogue_data:
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    find_cnt += 1
                    if self._is_say_block(b):
                        _update_dialogue(v['identifier'], i, b['new_code'], b['type'])
                    else:
                        # for non-Say statement, must match its type
                        if not say_only:
                            _update_dialogue(v['identifier'], i, b['new_code'], b['type'])
        for v in source_string_data:
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    find_cnt += 1
                    _update_string(v['identifier'], i, b['new_code'])

        # write updated translations to db
        dlang, slang = self._get_table_name(lang)
        self._update_batch(dlang, updated_ddocids, ddocid_map)
        self._update_batch(slang, updated_sdocids, sdocid_map)
        # update statistics when updating translation
        self.update_translation_stats(lang, say_only=say_only)
        print(f'{lang}: {len(updated_ddocids)} updated dialogue translations, '
              f'{len(updated_sdocids)} updated string translations. '
              f'[use:{use_cnt}, discord:{find_cnt - use_cnt}, total:{find_cnt}]')

    @db_context
    def update_translations(self, lang: str, translated_lines: List[Tuple[str, str]],
                            untranslated_only=True, discord_blank=True, say_only: bool = True):
        '''
        update translation of the specified language

        :param lang: language
        :param translated_lines: List[(tid, translated_line)]
        :param untranslated_only: If False, update all translated and untranslated lines.
                                  Otherwise, untranslated ones only
        :param discord_blank: discord blank or empty texts
        :param say_only: only update Say statement
        :return:
        '''
        if not translated_lines:
            print('No data to update')
            return
        lang = assert_not_blank(lang, 'lang')
        if not self.exists_lang(lang):
            print(f'No translations of language {lang}, please import it first')
            return
        dialogue_data, string_data = self._list_translations(lang)

        # get all untranslations first, mapped by tid
        tid_dblock_map = dict()
        tid_sblock_map = dict()
        ddocid_map = dict()
        sdocid_map = dict()
        for v in dialogue_data:
            ddocid_map[v.doc_id] = v['block']
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None and untranslated_only:
                    continue
                if not self._is_say_block(b) and say_only:
                    continue
                tid_dblock_map[self._encode_tid(self.DIALOGUE_ID_PREFIX, i, v.doc_id)] = b
        for v in string_data:
            sdocid_map[v.doc_id] = v['block']
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None and untranslated_only:
                    continue
                tid_sblock_map[self._encode_tid(self.STRING_ID_PREFIX, i, v.doc_id)] = b

        if len(tid_dblock_map) == 0 and len(tid_sblock_map) == 0:
            print(f'No translations of language {lang} to be updated')
            return

        # record updated doc_id
        updated_ddocids = set()
        updated_sdocids = set()
        updating_cnt = 0
        for tid, new_code in translated_lines:
            if tid is None or new_code is None:
                continue
            p, _, doc_id = self._decode_tid(tid)
            if p:
                block = None
                updated_docids = None
                # doc_id = None
                if p == self.DIALOGUE_ID_PREFIX:
                    block = tid_dblock_map.get(tid, None)
                    updated_docids = updated_ddocids
                elif p == self.STRING_ID_PREFIX:
                    block = tid_sblock_map.get(tid, None)
                    updated_docids = updated_sdocids
                if block:
                    if discord_blank and new_code.strip() == '':
                        continue
                    if self._is_user_block(block):
                        new_code = self._to_userblock_text(block, to_string_text(new_code))
                        block['new_code'] = new_code
                    else:
                        block['new_code'] = to_string_text(new_code)
                    updating_cnt += 1
                    updated_docids.add(doc_id)

        # write updated translation to db
        dlang, slang = self._get_table_name(lang)
        self._update_batch(dlang, updated_ddocids, ddocid_map)
        self._update_batch(slang, updated_sdocids, sdocid_map)
        # update statistics when updating translation
        if updated_ddocids or updated_sdocids:
            self.update_translation_stats(lang, say_only=say_only)
        print(f'{lang}: {len(updated_ddocids)} updated dialogue translations, '
              f'{len(updated_sdocids)} updated string translations. '
              f'[use:{updating_cnt}, discord:{len(translated_lines) - updating_cnt}, total:{len(translated_lines)}]')

    def _update_batch(self, table_name, updated_docids, docid_map):
        ids, blocks = [], []
        for did in updated_docids:
            ids.append(did)
            blocks.append(docid_map[did])
        with self._open_db() as dao:
            dao.update_blocks(table_name, ids, blocks)

    @db_context
    def import_translations(self, lang: str, translated_only: bool = True, say_only: bool = True):
        lang = assert_not_blank(lang, 'lang')
        if translated_only:
            # check if there exists the 'game/tl/{language}'
            tl_dir = os.path.join(self._project.tl_dir, lang)
            if not exists_dir(os.path.join(self._project.tl_dir, lang)):
                print(f'No translations of language {lang} in {tl_dir}')
                return
        data, msg = _get_task_result(get_translations(self._project, None, lang,
                                                      ignore=default_config['index']['ignore'],
                                                      translated_only=translated_only, say_only=say_only))
        dialogue_data = data['dialogues']
        string_data = data['strings']
        with self._open_db() as dao:
            self.drop_translations(lang)
            dlang, slang = self._get_table_name(lang)
            dao.add_batch(dlang, dialogue_data)
            dao.add_batch(slang, string_data)
            # update statistics when updating translation
            self.update_translation_stats(lang, say_only=say_only)
        print(msg)

    @db_context
    def export_translations(self, lang: str, translated_only: bool = True, say_only: bool = True):
        lang = assert_not_blank(lang, 'lang')
        if not self.exists_lang(lang):
            print(f'No {lang} translations to export')
            return
        dialogue_data, string_data = self._list_translations(lang)
        new_dialogue_data, new_string_data = [], []
        for v in dialogue_data:
            new_block = []
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    if self._is_say_block(b):
                        new_block.append(b)
                    else:
                        if not say_only:
                            new_block.append(b)
            if new_block:
                new_v = v.copy()
                new_v['block'] = new_block
                new_dialogue_data.append(new_v)
        for v in string_data:
            for i, b in enumerate(v['block']):
                if b['new_code'] is not None:
                    new_string_data.append(v)
        if len(new_dialogue_data) == 0 and len(new_string_data) == 0:
            print(f'No {lang} translations in this TranslationIndex to export')
            if translated_only:
                return
        print(f'{lang}: {len(new_dialogue_data)} dialogue and {len(new_string_data)} string translations '
              f'are ready to export')
        affected_files, msg = _get_task_result(generate_translations(self._project, {
            'dialogues': new_dialogue_data,
            'strings': new_string_data,
        }, lang, translated_only=translated_only, say_only=say_only, ignore=default_config['index']['ignore']))
        if affected_files:
            print('We have written translations to these following files:')
            for f in affected_files:
                print('\t', f)
        print(msg)

    def count_translations(self, lang: str, show_detail: bool = False, say_only: bool = True):
        lang = assert_not_blank(lang, 'lang')
        data, msg = _get_task_result(count_translations(self._project, None, lang, say_only=say_only))
        dialogue_data = data['dialogues']
        string_data = data['strings']
        dialogue_cnt_map = defaultdict(int)
        string_cnt_map = defaultdict(int)

        if show_detail:
            print('Missing dialogues<<<<<<<<<<<<')
        for d in dialogue_data:
            if show_detail:
                print(f'{d["filename"]}:{d["linenumber"]}')
            for b in d['block']:
                if show_detail:
                    print('\t', b['what'] if self._is_say_block(b) else b['code'])
                dialogue_cnt_map[d["filename"]] += 1
        if show_detail:
            print('Missing strings<<<<<<<<<<<<')
        for d in string_data:
            if show_detail:
                print(f'{d["filename"]}:{d["linenumber"]}')
            for b in d['block']:
                if show_detail:
                    print('\t', b['what'])
                string_cnt_map[d["filename"]] += 1

        if len(dialogue_cnt_map) > 0:
            print('Miss dialogue translations in:')
            for f, c in dialogue_cnt_map.items():
                print('\t', f'{f}: {c}')
        if len(dialogue_cnt_map) > 0:
            print('Miss string translations in:')
            for f, c in string_cnt_map.items():
                print('\t', f'{f}: {c}')
        print(msg)

    def to_dict(self):
        return {
            'project': {
                'project_path': self._project.project_path,
                'executable_path': self._project.executable_path,
                'project_name': self._project.project_name,
                'game_info': self._project.game_info,
                'injection_state': self._project.__getattribute__('_injection_state'),
            },
            'nickname': self._nickname,
            'tag': self._tag,
            'stats': self._stats,
            'db_file': self._db_file,
        }

    @classmethod
    def from_dict(cls, data: dict):
        pdata = data['project']
        project = Project(project_path=pdata['project_path'], executable_path=pdata['executable_path'],
                          project_name=pdata['project_name'], game_info=pdata['game_info'],
                          injection_state=pdata['injection_state'])
        new_inst = cls(
            project=project,
            nickname=data['nickname'],
            tag=data['tag'],
            stats=data.get('stats', None),
            db_file=data['db_file']
        )
        if hasattr(data, 'doc_id'):
            new_inst._doc_id = data.__getattribute__('doc_id')
        return new_inst

    @staticmethod
    def check_existing_with(nickname: str, tag: str, check_dbfiles: bool = True, exclude_docid: int = None):
        nickname = assert_not_blank(nickname)
        tag = strip_or_none(tag)

        # check among current db files to make sure not to overwrite a existing one
        if check_dbfiles:
            current_name = f'projz_{nickname}_{tag}.db'
            db_files = sorted(glob.glob(os.path.join(default_config.project_path, '*.db')))
            for f in db_files:
                assert os.path.basename(f) != current_name, (
                    f'A file named "{current_name}" in {default_config.project_path} found. '
                    f'Please reassign another value for nickname({nickname}) or tag({tag})')
        # then check in the db
        with TranslationIndexDao() as dao:
            assert not dao.contains({'nickname': nickname, 'tag': tag}, exclude_docid), (
                f'A TranslationIndex with same nickname({nickname}) and tag({tag}) found. '
                f'Please reassign another value for nickname or tag')
        return nickname, tag

    @classmethod
    def from_dir(cls, project_path: str, nickname: str = None, tag: str = None):
        nickname = strip_or_none(nickname)
        if not nickname:
            nickname = ''.join(random.sample(uuid.uuid1().hex, 8))
            print(f'The blank nickname is set to "{nickname}"')
        nickname, tag = cls.check_existing_with(nickname, tag)
        project = Project.from_dir(project_path)
        return cls(
            project=project,
            nickname=nickname,
            tag=tag
        )

    @db_context
    def save(self):
        # if it exists in db, update it
        if self._doc_id is not None:
            self._update(self.to_dict())
        else:
            # we don't want duplicate name and tag
            nickname, tag = self.check_existing_with(self.nickname, self.tag)
            self._nickname = nickname
            self._tag = tag
            # Otherwise, save it to db
            with TranslationIndexDao() as dao:
                doc_id = dao.add(self.to_dict())
                self._doc_id = doc_id

    @db_context
    def _update(self, data: dict):
        assert self._doc_id is not None, 'Please save the TranslationIndex first'
        if data is None or len(data) == 0:
            return
        nickname = data.get('nickname', None)
        tag = data.get('tag', None)
        if nickname or tag:
            if nickname is None:
                nickname = self._nickname
            if tag is None:
                tag = self._tag
            # we don't want duplicate name and tag
            nickname, tag = self.check_existing_with(nickname, tag, False, self.doc_id)
            data['nickname'] = nickname
            data['tag'] = tag
        with TranslationIndexDao() as dao:
            dao.update(data, self._doc_id)
            self._nickname = nickname
            self._tag = tag

    @classmethod
    def from_docid_or_nickname(cls, doc_id: int = None, nickname: str = None):
        if doc_id is None and nickname is None:
            return None
        with TranslationIndexDao() as dao:
            p = dao.select_first(doc_id, nickname)
            if p:
                return TranslationIndex.from_dict(p)
        return None

    @staticmethod
    def list_indexes():
        with TranslationIndexDao() as dao:
            res = dao.list()
        return [(i[0], TranslationIndex.from_dict(i[1])) for i in res]

    @staticmethod
    def remove_index(doc_id: int = None, nickname: str = None):
        if doc_id is None and nickname is None:
            return True
        with TranslationIndexDao() as dao:
            p = dao.select_first(doc_id, nickname)
            if p is not None:
                dao.delete(p.doc_id, nickname=None)
                print(f'TranslationIndex({p["nickname"]}:{p["tag"]}) is deleted.')
                db_file = p.get('db_file', None)
                if db_file and exists_file(db_file):
                    os.remove(db_file)
                    print(f'{db_file} is deleted.')
        return True

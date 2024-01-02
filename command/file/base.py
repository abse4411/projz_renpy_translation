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
import os
from typing import Dict

from command import BaseIndexCmd
from store import TranslationIndex
from store.database.base import db_context
from store.group import ALL, TRANS, UNTRANS, group_translations_by, ALL_FIELDS, GROUPBY_FIELDS, SORTBY_FIELDS
from util import exists_file, mkdir


class SaveFileBaseCmd(BaseIndexCmd):
    def __init__(self, name: str, file_type: str, file_ext: str):
        description = f'Save untranslated lines of the give language to a {file_type} file.'
        super().__init__(name, description)
        self.file_type = file_type
        self.file_ext = file_ext
        self._parser.add_argument("-l", "--lang", required=True, type=str, metavar='language',
                                  help="The language to save.")
        save_filename = os.path.join(self.config.project_path, file_type, f'nickname_tag.{file_ext}')
        self._parser.add_argument("-f", "--file", required=False, type=str, metavar=f'{file_type}_file',
                                  help=f"The filename to save the generated {file_type} file."
                                       f" if not presented, it will save to {save_filename}.")
        self._parser.add_argument("-ab", "--accept_blank", action='store_true',
                                  help="Accept blank untranslated lines to write to the file.")

    def check_savefile_and_index(self):
        save_file = self.args.file
        if save_file:
            assert exists_file(save_file), f'{self.args.file} not found.'
            index = self.get_translation_index()
        else:
            save_dir = os.path.join(self.config.project_path, self.file_type)
            mkdir(save_dir)
            index = self.get_translation_index()
            save_file = os.path.join(save_dir, f'{index.nickname}_{index.tag}_{self.args.lang}.{self.file_ext}')
        return save_file, index

    @db_context
    def check_untranslated_lines(self):
        save_file, index = self.check_savefile_and_index()
        tids_and_texts = index.get_untranslated_lines(self.args.lang, say_only=True)
        res = []
        if tids_and_texts:
            accept_blank = self.args.accept_blank
            if tids_and_texts:
                for tid, raw_text in tids_and_texts:
                    if raw_text.strip() == '' and not accept_blank:
                        continue
                    res.append([tid, raw_text])
        if len(res) == 0:
            print('No untranslated lines to save.')
        return save_file, index, res


class DumpToFileBaseCmd(BaseIndexCmd):
    def __init__(self, name: str, file_type: str, file_ext: str):
        description = f'Dump translations of the give language to a {file_type} file.'
        super().__init__(name, description)
        self.file_type = file_type
        self.file_ext = file_ext
        self._parser.add_argument("-l", "--lang", required=True, type=str, metavar='language',
                                  help="The language to save.")
        save_filename = os.path.join(self.config.project_path, file_type, f'nickname_tag.{file_ext}')
        self._parser.add_argument("-f", "--file", required=False, type=str, metavar=f'{file_type}_file',
                                  help=f"The filename to save the generated {file_type} file."
                                       f" if not presented, it will save to {save_filename}.")
        self._parser.add_argument("-s", "--scope", choices=[ALL, TRANS, UNTRANS], type=str, default=ALL,
                                  help="The scope of translations to dump. (all, translated, untranslated)")
        self._parser.add_argument("-g", "--group_by", choices=GROUPBY_FIELDS, type=str, default='filename',
                                  help="Grop translations by the field.")
        self._parser.add_argument("-sk", "--sort_key", choices=SORTBY_FIELDS, type=str, default='linenumber',
                                  help="Sort translations in group by the field.")
        self._parser.add_argument("-r", "--reverse", action='store_true',
                                  help="Use a reverse order in sorting.")

    def check_savefile_and_index(self):
        save_file = self.args.file
        if save_file:
            assert exists_file(save_file), f'{self.args.file} not found.'
            index = self.get_translation_index()
        else:
            save_dir = os.path.join(self.config.project_path, self.file_type)
            mkdir(save_dir)
            index = self.get_translation_index()
            save_file = os.path.join(save_dir, f'{index.nickname}_{index.tag}_{self.args.lang}_dump.{self.file_ext}')
        return save_file, index

    @db_context
    def get_dump_data(self):
        save_file, index = self.check_savefile_and_index()
        group_map = group_translations_by(self.args.group_by, self.args.sort_key, self.args.scope,
                                          index, self.args.lang, reverse=self.args.reverse, say_only=True)
        if len(group_map) == 0:
            print('No translations to dump.')
        return save_file, index, group_map


class LoadFileBaseCmd(BaseIndexCmd):
    def __init__(self, name: str, file_type: str, file_ext: str):
        description = f'Load translated lines of the give language from a {file_type} file.'
        super().__init__(name, description)
        self.file_type = file_type
        self.file_ext = file_ext
        self._parser.add_argument("-l", "--lang", required=True, type=str, metavar='language',
                                  help="The language to load.")
        save_filename = os.path.join(self.config.project_path, file_type, f'nickname_tag.{file_ext}')
        self._parser.add_argument("-f", "--file", required=False, type=str, metavar=f'{file_type}_file',
                                  help="The filename to load translated {file_type} file. if not presented, "
                                       f"we will read from {save_filename}.")
        self._parser.add_argument("-ab", "--accept_blank", action='store_true',
                                  help="Accept blank translated lines from the file.")
        self._parser.add_argument("-v", "--verbose", action='store_true',
                                  help="Print more details.")

    def check_untranslated_tidmap(self, index: TranslationIndex):
        tids_and_texts = index.get_untranslated_lines(self.args.lang, say_only=True)
        tid_map = {tid: text for tid, text in tids_and_texts}
        if not tid_map:
            print('No untranslated lines to update.')
        return tid_map

    def get_savefile_and_index(self):
        save_file = self.args.file
        if save_file:
            assert exists_file(save_file), f'{self.args.file} not found.'
            index = self.get_translation_index()
        else:
            save_dir = os.path.join(self.config.project_path, self.file_type)
            index = self.get_translation_index()
            save_file = os.path.join(save_dir, f'{index.nickname}_{index.tag}_{self.args.lang}.{self.file_ext}')
            assert exists_file(save_file), f'{self.args.file} not found.'
            print(f'Load {self.file_type} file from {save_file}')
        return save_file, index

    def get_translated_texts(self, tid_map: Dict[str, str], save_file: str):
        raise NotImplementedError()

    @db_context
    def invoke(self):
        save_file, index = self.get_savefile_and_index()
        tid_map = self.check_untranslated_tidmap(index)
        if tid_map:
            tids_and_texts = self.get_translated_texts(tid_map, save_file)
            if tids_and_texts:
                index.update_translations(self.args.lang, tids_and_texts,
                                          untranslated_only=True, discord_blank=not self.args.accept_blank)
            else:
                print('No translated lines to update.')


class UpdateFromFileBaseCmd(BaseIndexCmd):
    def __init__(self, name: str, file_type: str, file_ext: str):
        description = f'Update translations of the give language from a {file_type} file.'
        super().__init__(name, description)
        self.file_type = file_type
        self.file_ext = file_ext
        self._parser.add_argument("-l", "--lang", required=True, type=str, metavar='language',
                                  help="The language to load.")
        save_filename = os.path.join(self.config.project_path, file_type, f'nickname_tag.{file_ext}')
        self._parser.add_argument("-f", "--file", required=False, type=str, metavar=f'{file_type}_file',
                                  help="The filename to load translated {file_type} file. if not presented, "
                                       f"we will read from {save_filename}.")
        self._parser.add_argument("-ab", "--accept_blank", action='store_true',
                                  help="Accept blank translated lines from the file.")
        self._parser.add_argument("-v", "--verbose", action='store_true',
                                  help="Print more details.")

    def get_tidmap(self, index: TranslationIndex):
        tids_and_utexts = index.get_untranslated_lines(self.args.lang, say_only=True)
        tids_and_ttexts = index.get_translated_lines(self.args.lang, say_only=True)
        tid_map = {tid: text for tid, text in tids_and_ttexts + tids_and_utexts}
        if not tid_map:
            print('No untranslated lines to update.')
        return tid_map

    def get_savefile_and_index(self):
        save_file = self.args.file
        if save_file:
            assert exists_file(save_file), f'{self.args.file} not found.'
            index = self.get_translation_index()
        else:
            save_dir = os.path.join(self.config.project_path, self.file_type)
            index = self.get_translation_index()
            save_file = os.path.join(save_dir, f'{index.nickname}_{index.tag}_{self.args.lang}_dump.{self.file_ext}')
            assert exists_file(save_file), f'{self.args.file} not found.'
            print(f'Load {self.file_type} file from {save_file}')
        return save_file, index

    def get_translations(self, tid_map: Dict[str, str], save_file: str):
        raise NotImplementedError()

    @db_context
    def invoke(self):
        save_file, index = self.get_savefile_and_index()
        tid_map = self.get_tidmap(index)
        tids_and_texts = self.get_translations(tid_map, save_file)
        if tids_and_texts:
            index.update_translations(self.args.lang, tids_and_texts,
                                      untranslated_only=False, discord_blank=not self.args.accept_blank)
        else:
            print('No translations to update.')

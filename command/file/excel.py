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
from collections import defaultdict
from typing import Dict, List

import pandas as pd
from pandas import ExcelWriter
import tqdm

from command import BaseIndexCmd, BaseLangIndexCmd
from command.file.base import SaveFileBaseCmd, LoadFileBaseCmd, DumpToFileBaseCmd, ALL_FIELDS, UpdateFromFileBaseCmd
from config import default_config
from store import TranslationIndex
from store.database.base import db_context
from store.inspect import detect_missing_vars_and_tags, PRESENT_FIELDS
from util import file_name, exists_file, mkdir

TID_STR = 'Translation id (Don\'t modify)'
RAW_TEXT_STR = 'Raw Text'
COL_NAMES = [TID_STR, RAW_TEXT_STR]

_say_only = default_config.say_only

class SaveExcelCmd(SaveFileBaseCmd):
    def __init__(self):
        super().__init__('saveexcel', 'excel', 'xlsx')

    def invoke(self):
        save_file, index, tids_and_texts = self.check_untranslated_lines()
        if tids_and_texts:
            global COL_NAMES, TID_STR, RAW_TEXT_STR
            excel_id_data = []
            excel_nt_data = []
            for tid, raw_text in tids_and_texts:
                excel_id_data.append(tid)
                excel_nt_data.append(raw_text)
            df = pd.DataFrame({TID_STR: excel_id_data,
                               RAW_TEXT_STR: excel_nt_data})
            df = df.reindex(columns=COL_NAMES)
            df.to_excel(save_file, index=False)
            print(f'{len(excel_id_data)} untranslated lines are saved to {save_file}.')


class LoadExcelCmd(LoadFileBaseCmd):
    def __init__(self):
        super().__init__('loadexcel', 'excel', 'xlsx')

    def get_translated_texts(self, tid_map: Dict[str, str], save_file: str):
        global COL_NAMES, TID_STR, RAW_TEXT_STR
        df = pd.read_excel(save_file, na_filter=False, header=None, skiprows=[0],
                           usecols=[0, 1], names=[TID_STR, RAW_TEXT_STR])
        use_cnt = 0
        discord_cnt = 0
        tids_and_texts = []
        accept_blank = self.args.accept_blank
        verbose = self.args.verbose
        for i, (tid, new_text) in enumerate(zip(df[TID_STR], df[RAW_TEXT_STR]), 2):
            tid, new_text = str(tid).strip(), str(new_text)
            if TranslationIndex.is_valid_tid(tid):
                raw_text = tid_map.get(tid, None)
                if raw_text is not None:
                    if new_text == raw_text:
                        if verbose:
                            print(f'Discard untranslated line[Line {i}]: {raw_text}')
                    else:
                        if new_text.strip() == '' and not accept_blank:
                            if verbose:
                                print(f'Discard blank line[Line {i}]: {new_text}')
                        else:
                            use_cnt += 1
                            tids_and_texts.append([tid, new_text])
                            continue
                discord_cnt += 1
        print(f'Find {use_cnt} translated lines, and discord {discord_cnt} lines')
        return tids_and_texts


def gather_by_keys(items: List[dict], keys: List[str]):
    key_dict = defaultdict(list)
    for i in items:
        for k in keys:
            key_dict[k].append(i.get(k, None))
    return key_dict


_COLS = ['tid', 'new_text', 'old_text', 'linenumber', 'identifier', 'filename']


def longest_common_prefix(strs: List[str]):
    lcp = ""
    for tmp in zip(*strs):
        if len(set(tmp)) == 1:
            lcp += tmp[0]
        else:
            break
    return lcp


class DumpExcelCmd(DumpToFileBaseCmd):

    def __init__(self):
        super().__init__('dumpexcel', 'excel', 'xlsx')
        self._parser.add_argument("--single", action='store_true',
                                  help="Dump all data in a single sheet.")

    def invoke(self):
        save_file, index, sorted_data = self.get_dump_data()
        if sorted_data:
            cnt = 0
            # we should remove path separators of filename when using filename as sheet name
            if self.args.group_by == 'filename':
                ryp_files = set(list(sorted_data.keys()))
                lcp = longest_common_prefix(list(ryp_files))
                new_sorted_data = dict()
                for f in sorted_data.keys():
                    if len(lcp) >= len(f):
                        short_name = file_name(f)
                    else:
                        short_name = f[len(lcp):]
                    # replace invalid character (/, :) by the underline:
                    short_name = (short_name
                                  .replace('/', '_')
                                  .replace('\\', '_')
                                  .replace(':', '_'))
                    new_sorted_data[short_name] = sorted_data[f]
                sorted_data = new_sorted_data
            global _COLS
            with ExcelWriter(save_file) as writer:
                if self.args.single:
                    new_data = []
                    for file, data in tqdm.tqdm(sorted_data.items(), total=len(sorted_data),
                                                desc='Collecting data...'):
                        new_data += data
                        cnt += len(data)
                    df = pd.DataFrame(gather_by_keys(new_data, _COLS))
                    df = df.reindex(columns=_COLS)
                    print('Writing to excel...')
                    df.to_excel(writer, index=False)
                else:
                    for file, data in tqdm.tqdm(sorted_data.items(), total=len(sorted_data),
                                                desc='Writing to excel...'):
                        df = pd.DataFrame(gather_by_keys(data, _COLS))
                        df = df.reindex(columns=_COLS)
                        cnt += len(df)
                        df.to_excel(writer, sheet_name=file.strip(), index=False)
            print(f'{cnt} translations are dump to {save_file}.')


class DumpErrorExcelCmd(BaseLangIndexCmd):
    def __init__(self):
        description = f'Inspect each translated line to find missing vars or tags,\n' \
                      f'then save these error lines to a excel file. You can use the\n' \
                      f'updateexcel command to update translations after you fix them.'
        super().__init__('inspect', description)
        self.file_type = 'excel'
        self.file_ext = 'xlsx'
        save_filename = os.path.join(self.config.project_path, self.file_type,
                                     f'nickname_tag_lang_dump.{self.file_ext}')
        self._parser.add_argument("-f", "--file", required=False, type=str, metavar=f'{self.file_type}_file',
                                  help=f"The filename to save the generated {self.file_type} file."
                                       f" if not presented, it will save to {save_filename}.")

    def check_savefile_and_index(self):
        save_file = self.args.file
        if save_file:
            index = self.get_translation_index()
        else:
            save_dir = os.path.join(self.config.project_path, self.file_type)
            mkdir(save_dir)
            index = self.get_translation_index()
            save_file = os.path.join(save_dir, f'{index.nickname}_{index.tag}_{self.args.lang}_dump.{self.file_ext}')
            save_file = os.path.abspath(save_file)
        return save_file, index

    @db_context
    def invoke(self):
        save_file, index = self.check_savefile_and_index()
        error_translations = detect_missing_vars_and_tags(index, self.args.lang, say_only=_say_only)
        if error_translations:
            new_cols = ['tid', 'new_text', 'raw_text', 'message', 'identifier', 'filename', 'linenumber']
            excel_data = gather_by_keys(error_translations, PRESENT_FIELDS)

            df = pd.DataFrame(excel_data)
            df = df.reindex(columns=new_cols)
            df.to_excel(save_file, index=False)
            print(f'{len(error_translations)} error lines are saved to {save_file}.')
        else:
            print('Congratulations! No missing vars or tags found in translated lines.')


class UpdateExcelCmd(UpdateFromFileBaseCmd):

    def __init__(self):
        super().__init__('updateexcel', 'excel', 'xlsx')

    def get_translations(self, tid_map: Dict[str, str], save_file: str):
        use_cnt = 0
        discord_cnt = 0
        tids_and_texts = []
        accept_blank = self.args.accept_blank
        verbose = self.args.verbose
        df = pd.read_excel(save_file, sheet_name=None, na_filter=False)
        for sheet in tqdm.tqdm(df.keys(), total=len(df), desc='Reading from excel...'):
            sheet_data = df[sheet]
            for i, (tid, new_text) in enumerate(zip(sheet_data['tid'], sheet_data['new_text']), 1):
                tid, new_text = str(tid), str(new_text)
                if TranslationIndex.is_valid_tid(tid):
                    raw_text = tid_map.get(tid, None)
                    if raw_text is not None:
                        if new_text == raw_text:
                            if verbose:
                                print(f'Discard untranslated line[{sheet}, Line {i}]: {raw_text}')
                        else:
                            if new_text.strip() == '' and not accept_blank:
                                if verbose:
                                    print(f'Discard blank line[{sheet}, Line {i}]: {new_text}')
                            else:
                                use_cnt += 1
                                tids_and_texts.append([tid, new_text])
                                continue
                    discord_cnt += 1
        print(f'Find {use_cnt} translated lines, and discord {discord_cnt} lines')
        return tids_and_texts

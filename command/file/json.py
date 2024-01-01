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
from typing import Dict

from command.file.base import SaveFileBaseCmd, LoadFileBaseCmd
from store import TranslationIndex
from util import default_write, default_read


class SaveJsonCmd(SaveFileBaseCmd):
    def __init__(self):
        super().__init__('savejson', 'json', 'json')

    def invoke(self):
        save_file, index, tids_and_texts = self.check_untranslated_lines()
        if tids_and_texts:
            json_arr = []
            for tid, raw_text in tids_and_texts:
                json_arr.append({
                    'tid': tid,
                    'raw_text': raw_text,
                })
            with default_write(save_file) as f:
                json.dump(json_arr, f, ensure_ascii=False, indent=2)
            print(f'{len(json_arr)} untranslated lines are saved to {save_file}.')


class LoadJsonCmd(LoadFileBaseCmd):
    def __init__(self):
        super().__init__('loadjson', 'json', 'json')

    def get_translated_texts(self, tid_map: Dict[str, str], save_file: str):
        with default_read(save_file) as f:
            data = json.load(f)
        use_cnt = 0
        discord_cnt = 0
        tids_and_texts = []
        accept_blank = self.args.accept_blank
        for i, l in enumerate(data):
            tid = l.get('tid', None)
            new_text = l.get('raw_text', None)
            if tid is not None and new_text is not None:
                if TranslationIndex.is_valid_tid(tid):
                    raw_text = tid_map.get(tid, None)
                    if raw_text is not None:
                        if new_text == raw_text:
                            print(f'Discard untranslated line[Line {i}]: {raw_text}')
                        else:
                            if new_text.strip() == '' and not accept_blank:
                                print(f'Discard blank line[Line {i}]: {raw_text}')
                            else:
                                use_cnt += 1
                                tids_and_texts.append([tid, new_text])
                                continue
                    discord_cnt += 1
        print(f'Find {use_cnt} translated lines, and discord {discord_cnt} lines')
        return tids_and_texts

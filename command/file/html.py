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
import re
from typing import Dict

from command.file.base import SaveFileBaseCmd, LoadFileBaseCmd
from store import TranslationIndex
from util import default_write, default_read

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
{filler}
<br />
<div></div>
<div></div>
<div></div>
</body>
</html>
'''
DIV_TEMPLATE = '<!--{id}#PROJZ#--><div>{text}</div><!--PROJZ-->\n'
HTML_TAG = re.compile(r'<[^>]+>', re.S)


class SaveHtmlCmd(SaveFileBaseCmd):
    def __init__(self):
        super().__init__('savehtml', 'html', 'html')

    def invoke(self):
        save_file, index, tids_and_texts = self.check_untranslated_lines()
        if tids_and_texts:
            div_arr = []
            for tid, raw_text in tids_and_texts:
                div_arr.append(DIV_TEMPLATE.format(id=tid, text=raw_text))
            save_html = HTML_TEMPLATE.format(filler=''.join(div_arr))
            with default_write(save_file) as f:
                f.write(save_html)
            print(f'{len(div_arr)} untranslated lines are saved to {save_file}.')


class LoadHtmlCmd(LoadFileBaseCmd):
    def __init__(self):
        super().__init__('loadhtml', 'html', 'html')

    def get_translated_texts(self, tid_map: Dict[str, str], save_file: str):
        with default_read(save_file) as f:
            lines = f.readlines()
        use_cnt = 0
        discord_cnt = 0
        tids_and_texts = []
        accept_blank = self.args.accept_blank
        verbose = self.args.verbose
        for i, l in enumerate(lines):
            l = l.strip()
            if l:
                if l.startswith('<!--') and l.endswith('<!--PROJZ-->'):
                    tid_from = len('<!--')
                    tid_end = l.find('#PROJZ#-->')
                    if tid_from < tid_end:
                        tid = l[tid_from:tid_end]
                        new_text = HTML_TAG.sub('', l[tid_end + len('#PROJZ#-->'):])
                        if TranslationIndex.is_valid_tid(tid):
                            raw_text = tid_map.get(tid, None)
                            if raw_text is not None:
                                if new_text == raw_text:
                                    if verbose:
                                        print(f'Discard untranslated line[Line {i}]: {raw_text}')
                                else:
                                    if new_text.strip() == '' and not accept_blank:
                                        if verbose:
                                            print(f'Discard blank line[Line {i}]: {raw_text}')
                                    else:
                                        use_cnt += 1
                                        tids_and_texts.append([tid, new_text])
                                        continue
                            discord_cnt += 1
        print(f'Find {use_cnt} translated lines, and discord {discord_cnt} lines')
        return tids_and_texts

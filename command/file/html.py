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
from typing import Dict, List, Tuple

from command.file.base import SaveFileBaseCmd, LoadFileBaseCmd
from store import TranslationIndex
from util import default_write, default_read
from bs4 import BeautifulSoup
import html

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
DIV_TEMPLATE = '<p tid="{tid}">{text}</p>\n'
HTML_TAG = re.compile(r'<[^>]+>', re.S)

class SaveHtmlCmd(SaveFileBaseCmd):
    def __init__(self):
        super().__init__('savehtml', 'html', 'html')

    def save(self, save_file: str, index: TranslationIndex, tids_and_texts: List[Tuple[str, str]]):
        div_arr = []
        for tid, raw_text in tids_and_texts:
            div_arr.append(DIV_TEMPLATE.format(tid=tid, text=html.escape(raw_text)))
        save_html = HTML_TEMPLATE.format(filler=''.join(div_arr))
        with default_write(save_file) as f:
            f.write(save_html)


class LoadHtmlCmd(LoadFileBaseCmd):
    def __init__(self):
        super().__init__('loadhtml', 'html', 'html')

    def get_translated_texts(self, tid_map: Dict[str, str], save_file: str):
        with default_read(save_file) as f:
            html_doc = f.read()
        use_cnt = 0
        discord_cnt = 0
        tids_and_texts = []
        accept_blank = self.args.accept_blank
        verbose = self.args.verbose
        soup = BeautifulSoup(html_doc, 'html.parser')
        p_tags_with_tid = soup.find_all('p', attrs={'tid': True})
        for p in p_tags_with_tid:
            tid = p.get('tid')
            new_text = p.get_text()
            if tid is not None and new_text is not None:
                if TranslationIndex.is_valid_tid(tid):
                    raw_text = tid_map.get(tid, None)
                    if raw_text is not None:
                        if new_text == raw_text:
                            if verbose:
                                print(f'Discard untranslated line[tid: {tid}]: {raw_text}')
                        else:
                            if new_text.strip() == '' and not accept_blank:
                                if verbose:
                                    print(f'Discard blank line[tid: {tid}]: {raw_text}')
                            else:
                                use_cnt += 1
                                tids_and_texts.append([tid, new_text])
                                continue
                    discord_cnt += 1
        print(f'Find {use_cnt} translated lines, and discord {discord_cnt} lines')
        return tids_and_texts

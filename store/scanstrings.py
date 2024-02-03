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
import os.path
import re
from collections import defaultdict

from config import default_config
from store import TranslationIndex
from util import exists_file, default_read, exists_dir, walk_and_select, strip_or_none

# match for: translate chinese nikiinvite2_442941ca_1:"
_regex_trans = re.compile(r'^translate[\t ]+(\S+)[\t ]+strings:\s+')
# match fo: old "RenPy机翻工具"
_regex_str = re.compile(r'^([\t ]+)(\S+)[\t ]+"(.*)"\s*')
_new_str = 'new'
_old_str = 'old'


def _match_string(line: str):
    if line:
        match = _regex_str.match(line)
        if match:
            blanks, key, content = match.groups()
            return blanks, key, content
    return None, None, None


def process_file(fn: str):
    if not exists_file(fn):
        return {}
    with default_read(fn) as f:
        lines = f.readlines()
    res = defaultdict(dict)
    old_info = None
    lang = None
    for i, l in enumerate(lines, 1):
        if l.startswith('\ufeff'):
            l = l[1:]
        sl = l.strip()
        if sl == '' or sl.startswith('#'):
            continue
        match = _regex_trans.match(l)
        if match:
            if old_info is None:
                lang = match.group(1)
                continue
        else:
            b, k, c = _match_string(l)
            if b is not None:
                if lang:
                    if k == _new_str:
                        if old_info:
                            ob, oc, oi = old_info
                            if b == ob:
                                lang_map = res[lang]
                                if oc in lang_map:
                                    raise RuntimeError(f'File "{fn}", line {i}: '
                                                       f'A translation for {oc}" already exists at line {oi}:\n{l}')
                                else:
                                    lang_map[oc] = c
                                    old_info = None
                                    continue
                            else:
                                raise RuntimeError(f'File "{fn}", line {i}: '
                                                   f'Inconsistent indentation at line {oi}:\n{l}')
                    elif k == _old_str:
                        if old_info is None:
                            old_info = b, c, i
                            continue
        raise RuntimeError(f'File "{fn}", line {i}: unexpected statement\n{l}')
    return res


def get_default_strings(tl_dir: str, lang: str):
    string_map = dict()
    lang = strip_or_none(lang)
    if lang:
        # tl_dir = default_config['index']['recycle_dir']
        if exists_dir(tl_dir):
            rpys = walk_and_select(tl_dir, select_fn=lambda x: x.endswith('.rpy'))
            for r in rpys:
                string_map.update(process_file(r)[lang])
    return string_map


def update_string(index: TranslationIndex, tl_dir: str, lang: str, say_only: bool = True,
                  discord_blank=True):
    string_map = get_default_strings(tl_dir, lang)
    print(f'{len(string_map)} string translation found at {tl_dir}')
    tids_and_texts = index.get_untranslated_lines(lang, say_only=say_only)
    updates = []
    for tid, text in tids_and_texts:
        if tid.startswith(TranslationIndex.STRING_ID_PREFIX):
            new_str = string_map.get(text, None)
            if new_str is not None:
                updates.append((tid, new_str))
    if updates:
        index.update_translations(lang, updates, say_only=say_only, discord_blank=discord_blank)
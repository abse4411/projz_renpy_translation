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
import logging
from typing import List

from injection.base import BaseInjector
from util import default_read, default_write, exists_file


def count_indentation(raw_line: str):
    # count how many spaces or tabs dose the line starts with
    # if using spaces for indentation
    if raw_line.strip() == '':
        return 0, None
    if raw_line.startswith(' '):
        for j, char in enumerate(raw_line):
            if char != ' ':
                break
        return j, ' '
    # else if using tabs
    elif raw_line.startswith('\t'):
        for j, char in enumerate(raw_line):
            if char != '\t':
                break
        return j, '\t'
    # no indentation
    return 0, None


def find_codes(raw_codes: List[str], anchor_codes: List[str]):
    anchor_codes = [i.strip() for i in anchor_codes if i.strip() != '']
    assert len(anchor_codes) > 0, 'All code lines are blank!'
    len_anchor = len(anchor_codes)
    current_match_idx = 0
    start_idx = None
    end_idx = None

    for lineno, raw_line in enumerate(raw_codes):
        striped_line = raw_line.strip()
        # if a comment or a blank line
        if striped_line == '':
            continue
        else:
            if current_match_idx < len_anchor:
                if striped_line == anchor_codes[current_match_idx]:
                    current_match_idx += 1
                    if start_idx is None:
                        start_idx = lineno
                    if current_match_idx == len_anchor:
                        end_idx = lineno + 1
                        # we matched all these anchor codes, then we don't need to find another one
                        # don't use break !!!
                        current_match_idx += 1
                else:
                    current_match_idx = 0
                    start_idx = None
                    end_idx = None
    return start_idx, end_idx


def get_indented_code(raw_codes: List[str], target_codes: List[str], raw_lineno, indent_offset=0):
    raw_indent_info = [count_indentation(i) for i in raw_codes]
    target_indent_info = [count_indentation(i) for i in target_codes]

    def get_indent_level(indent_info):
        space_indent_set = {0}
        tab_indent_set = {0}
        for icount, ichar in indent_info:
            if ichar == ' ':
                space_indent_set.add(icount)
            elif ichar == '\t':
                tab_indent_set.add(icount)
        space_level = [i for i in sorted(list(space_indent_set))]
        tab_level = [i for i in sorted(list(tab_indent_set))]
        assert not (len(space_level) > 1 and len(tab_level) > 1), 'space and tab indentation found'
        if len(space_level) > 1:
            return space_level
        return tab_level

    def indentation_of(level, ichar, indent_level):
        if level > len(indent_level):
            if ichar == ' ':
                # indented by 4 spaces
                return ichar * (indent_level[-1] + 4 * (level - len(indent_level)))
            else:
                # indented by a tab
                return ichar * (indent_level[-1] + 1 * (level - len(indent_level)))
        else:
            return ichar * indent_level[level]

    raw_indent_lvl = get_indent_level(raw_indent_info)
    raw_lvlmap = {i: l for l, i in enumerate(raw_indent_lvl)}
    target_lvlmap = {i: l for l, i in enumerate(get_indent_level(target_indent_info))}

    indent_count, indent_char = raw_indent_info[raw_lineno]
    base_level = raw_lvlmap[indent_count]
    base_level += indent_offset
    if base_level < 0:
        raise IndexError(f'Indentation level should be not less than 0')
    indented_code = []
    for lineno, code in enumerate(target_codes):
        striped_code = code.strip()
        # if a comment or a blank line
        if striped_code == '' or striped_code.startswith('#'):
            indented_code.append(code)
        else:
            indent_str = indentation_of(base_level + target_lvlmap[target_indent_info[lineno][0]],
                                        indent_char, raw_indent_lvl)
            indented_code.append(indent_str + code.strip())
    return indented_code


def line_strip(lines: List[str]):
    start_idx = 0
    while start_idx < len(lines):
        if lines[start_idx].strip() != '':
            break
        start_idx += 1
    end_idx = len(lines) - 1
    while end_idx >= 0:
        if lines[end_idx].strip() != '':
            break
        end_idx -= 1
    return lines[start_idx:end_idx + 1]


class PyCodeInjector(BaseInjector):
    def __init__(self, filename, anchor_codes: List[str], target_codes: List[str],
                 insert_before: bool = True, indent_offset: int = 0, newline='\n'):
        self.filename = filename
        self.anchor_codes = line_strip(anchor_codes)
        assert len(self.anchor_codes) > 0, 'All anchor codes lines are blank!'
        self.target_codes = line_strip(target_codes)
        assert len(self.target_codes) > 0, 'All target codes lines are blank!'
        self.insert_before = insert_before
        self.indent_offset = indent_offset
        self.newline = newline

    def __call__(self, *args, **kwargs):
        if not exists_file(self.filename):
            logging.error(f'{self.filename} not found')
            return False
        with default_read(self.filename) as f:
            raw_codes = f.readlines()
        (start_idx, _) = find_codes(raw_codes, self.target_codes)
        # if already injecting
        if start_idx is not None:
            return True
        (start_idx, end_idx) = find_codes(raw_codes, self.anchor_codes)
        # print((start_idx, end_idx))
        if start_idx is None:
            return False
        # if finding anchor codes, start to inject target codes
        if self.insert_before:
            res_code = get_indented_code(raw_codes, self.target_codes, start_idx, self.indent_offset)
            new_codes = raw_codes[:start_idx] + [c + self.newline for c in res_code] + raw_codes[start_idx:]
        else:
            res_code = get_indented_code(raw_codes, self.target_codes, end_idx, self.indent_offset)
            new_codes = raw_codes[:end_idx] + [c + self.newline for c in res_code] + raw_codes[end_idx:]
        with default_write(self.filename, newline=self.newline) as f:
            logging.info(f'Injecting code into {self.filename}')
            f.writelines(new_codes)
        return True

    def undo(self, *args, **kwargs):
        if not exists_file(self.filename):
            return True
        with default_read(self.filename) as f:
            raw_codes = f.readlines()
        (start_idx, end_idx) = find_codes(raw_codes, self.target_codes)
        # print((start_idx, end_idx))
        if start_idx is None:
            return True
        else:
            new_codes = raw_codes[:start_idx] + raw_codes[end_idx:]
        with default_write(self.filename, newline=self.newline) as f:
            logging.info(f'Undo code injection in {self.filename}')
            f.writelines(new_codes)
        return True

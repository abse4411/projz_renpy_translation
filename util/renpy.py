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
from collections import defaultdict

from util import strip_or_none

# match the variable
regex_var = re.compile(r'(\[[A-Za-z_]+[A-Za-z0-9_\.]*\])')
# match the tag
regex_tag = re.compile(r'\{[^}]*\}')
# match any alpha
alpha_re = re.compile(r'[A-Za-z]', re.S)


def list_vars(text: str):
    variables = defaultdict(int)
    text = strip_or_none(text)
    if text is not None:
        text = text.replace('[[', '\0').replace('\[', '\0')
        stack = []
        for i, c in enumerate(text):
            if c == '[':
                stack.append(i)
            elif c == ']':
                if stack:
                    start = stack.pop()
                    if len(stack) == 0:
                        variables[text[start:i + 1]] += 1
    return variables


def list_tags(text: str):
    variables = defaultdict(int)
    text = strip_or_none(text)
    if text is not None:
        text = text.replace('{{', '\0').replace('\{', '\0')
        stack = []
        for i, c in enumerate(text):
            if c == '{':
                stack.append(i)
            elif c == '}':
                if stack:
                    start = stack.pop()
                    if len(stack) == 0:
                        variables[text[start:i + 1]] += 1
    return variables


_ESCAPE_CHARS = ['\\"', '\\\'', '\\\\', '\\n', '\\%', '%%', '[[', '{{', '【【']


def list_escape_chars(text: str):
    global _ESCAPE_CHARS
    variables = defaultdict(int)
    text = strip_or_none(text)
    if text is not None:
        for c in _ESCAPE_CHARS:
            cnt = text.count(c)
            if cnt > 0:
                variables[c] = cnt
    return variables


def strip_tags(text: str):
    if text is not None:
        return regex_tag.sub('', text)
    return text


def contain_alpha(text: str):
    if text:
        return alpha_re.search(text) is not None
    return False

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

def strip_or_none(string: str):
    if string:
        string = string.strip()
        if string == '':
            return None
        return string
    return string


def assert_not_blank(string: str, name=None):
    string = strip_or_none(string)
    assert string, f'{name if name else "string"} should not be blank'
    return string


def quote_unicode(s):
    s = s.replace("\\", "\\\\")
    s = s.replace("\"", "\\\"")
    s = s.replace("\a", "\\a")
    s = s.replace("\b", "\\b")
    s = s.replace("\f", "\\f")
    s = s.replace("\n", "\\n")
    s = s.replace("\r", "\\r")
    s = s.replace("\t", "\\t")
    s = s.replace("\v", "\\v")

    return s


def unquote_unicode(s):
    s = s.replace("\\\\", "\\")
    s = s.replace("\\\"", "\"")
    s = s.replace("\\a", "\a")
    s = s.replace("\\b", "\b")
    s = s.replace("\\f", "\f")
    s = s.replace("\\n", "\n")
    s = s.replace("\\r", "\r")
    s = s.replace("\\t", "\t")
    s = s.replace("\\v", "\v")

    return s


def strip_linebreakers(text: str):
    if text:
        return text.replace('\r\n', '').replace('\n', '')
    return text


def to_string_text(text: str):
    if text:
        return unquote_unicode(text)
    return text


def to_translatable_text(text: str):
    if text:
        return quote_unicode(text)
    return text

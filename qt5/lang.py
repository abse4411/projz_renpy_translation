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

LANG = 'en'
LANG_MAP = {
    'en': 'qt5/i18n/EN',
    'zh-cn': 'qt5/i18n/zh_CN',
}


def set_lang(lang: str):
    global LANG
    if lang in LANG_MAP:
        LANG = lang


def get_lang_ts():
    global LANG
    ts = LANG_MAP.get(LANG, None)
    if ts is None:
        return LANG_MAP['en']
    return ts
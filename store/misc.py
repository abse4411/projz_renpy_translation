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

from util.renpy import list_tags


def ast_of(
        identifier=None,
        language=None,
        filename=None,
        linenumber=None,
        block=None
):
    return {
        'identifier': identifier,
        'language': language,
        'filename': filename,
        'linenumber': linenumber,
        'block': block if block is not None else [],
    }


def block_of(
        type=None,
        what=None,
        who=None,
        code=None,
        new_code=None,
        parsed=None,
):
    return {
        'type': type,
        'what': what,
        'who': who,
        'code': code,
        'new_code': new_code,
        'parsed': parsed if parsed is not None else [],
    }


def quote_with_fonttag(font_dir, font, text):
    if font:
        return f'{{font={font_dir}{font}}}{text}{{/font}}'
    return text

def quote_with_colortag(color, text):
    if color:
        return f'{{color={color}}}{text}{{/color}}'
    return text


def is_valid_hex_color(s, allow_short=True, require_hash=True):
    """
    判断字符串是否为合法的16进制颜色代码。

    参数:
        s (str): 要检查的字符串。
        allow_short (bool): 是否接受简写格式（如 #FFF）。默认 True。
        require_hash (bool): 是否要求必须以 # 开头。默认 True。

    返回:
        bool: 是否是有效的颜色代码。
    """
    if not isinstance(s, str):
        return False

    # 构建正则表达式
    hash_symbol = '#' if require_hash else '#?'

    if allow_short:
        pattern = f'^{hash_symbol}([A-Fa-f0-9]{{3}}){{1,2}}$'
    else:
        pattern = f'^{hash_symbol}[A-Fa-f0-9]{{6}}$'

    return re.fullmatch(pattern, s) is not None
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
from typing import List, Any

from injection import Project

"""
    This file provides a series of APIs for external call of resources/codes/projz_injection.py by injection.renpy.Project 
"""


def _get_base_args(lang: str = None, translated_only: bool = True, say_only: bool = False, strings_only: bool = False,
                   common_only: bool = False, ignore=None, **kwargs):
    args = []
    kwargs.pop('lang', None)
    kwargs.pop('translated_only', None)
    kwargs.pop('say_only', None)
    kwargs.pop('strings_only', None)
    kwargs.pop('common_only', None)
    kwargs.pop('ignore', None)
    if lang:
        args.append(f'--language')
        args.append(f'{lang}')
    if translated_only:
        args.append('--translated-only')
    if say_only:
        args.append('--say-only')
    if strings_only:
        args.append('--strings-only')
    if common_only:
        args.append('--common-only')
    if ignore:
        args.append(f'--ignore')
        for i in ignore:
            args.append(i)
    return args, kwargs


def get_translations(p: Project, payload: Any, lang: str, **kwargs):
    args, kwargs = _get_base_args(lang, **kwargs)
    return p.launch_task(payload, args=args, **kwargs)


def generate_translations(p: Project, payload: Any, lang: str, **kwargs):
    args, kwargs = _get_base_args(lang, **kwargs)
    args.append('--generate')
    return p.launch_task(payload, args=args, **kwargs)


def count_translations(p: Project, payload: Any, lang: str, **kwargs):
    args, kwargs = _get_base_args(lang, **kwargs)
    args.append('--count')
    return p.launch_task(payload, args=args, **kwargs)


def lang_project(p: Project, **kwargs):
    return p.launch('', args=[], **kwargs)

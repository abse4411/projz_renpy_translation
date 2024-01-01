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


def _add_count_arg(args: List[str]):
    args.append('--count')


def _add_generate_arg(args: List[str]):
    args.append('--generate')


def _add_sayonly_arg(args: List[str]):
    args.append('--say-only')


def _add_translatedonly_arg(args: List[str]):
    args.append('--translated-only')


def _add_language_arg(lang: str, args: List[str]):
    args.append(f'--language {lang}')


def _add_commononly_arg(args: List[str]):
    args.append('--common-only')


def _add_stringsonly_arg(args: List[str]):
    args.append('--strings-only')


def _get_base_args(lang: str = None, translated_only: bool = True, say_only: bool = False, strings_only: bool = False,
                   common_only: bool = False, **kwargs):
    args = []
    kwargs.pop('lang', None)
    kwargs.pop('translated_only', None)
    kwargs.pop('say_only', None)
    kwargs.pop('strings_only', None)
    kwargs.pop('common_only', None)
    if lang:
        _add_language_arg(lang, args)
    if translated_only:
        _add_translatedonly_arg(args)
    if say_only:
        _add_sayonly_arg(args)
    if translated_only:
        _add_translatedonly_arg(args)
    if strings_only:
        _add_stringsonly_arg(args)
    if common_only:
        _add_commononly_arg(args)
    return args, kwargs


def get_translations(p: Project, payload: Any, lang: str, **kwargs):
    args, kwargs = _get_base_args(lang, **kwargs)
    return p.launch_task(payload, args=args, **kwargs)


def generate_translations(p: Project, payload: Any, lang: str, **kwargs):
    args, kwargs = _get_base_args(lang, **kwargs)
    _add_generate_arg(args)
    return p.launch_task(payload, args=args, **kwargs)


def count_translations(p: Project, payload: Any, lang: str, **kwargs):
    args, kwargs = _get_base_args(lang, **kwargs)
    _add_count_arg(args)
    return p.launch_task(payload, args=args, **kwargs)


def lang_project(p: Project, **kwargs):
    return p.launch('', args=[], **kwargs)

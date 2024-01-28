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
import glob
import logging
import os
import shutil
from typing import List

from config import default_config
from injection.base import PyCodeInjector, FileInjector, BaseInjector
from injection.base.code import line_strip
from injection.base.file import PyFileInjector, RpyFileInjector
from util import walk_and_select, file_name, default_read, default_write, mkdir, exists_dir

PYTHON_WIN64_EXE = [
    'windows-x86_64/python.exe',
    'windows-x86_64/pythonw.exe',
    'py2-windows-x86_64/python.exe',
    'py2-windows-x86_64/pythonw.exe',
    'py3-windows-x86_64/python.exe',
    'py3-windows-x86_64/pythonw.exe',
]
PYTHON_WIN32_EXE = [
    'windows-x86_64/python.exe',
    'windows-x86_64/pythonw.exe',
    'py2-windows-i686/python.exe',
    'py2-windows-i686/pythonw.exe',
    'py3-windows-i686/python.exe',
    'py3-windows-i686/pythonw.exe',
]
PYTHON_LINUX64_EXE = [
    'linux-x86_64/python',
    'linux-x86_64/pythonw',
    'py2-linux-x86_64/python',
    'py2-linux-x86_64/pythonw',
    'py3-linux-x86_64/python',
    'py3-linux-x86_64/pythonw',
]
PYTHON_LINUX32_EXE = [
    'linux-i686/python',
    'linux-i686/pythonw',
    'py2-linux-i686/python',
    'py2-linux-i686/pythonw',
    'py3-linux-i686/python',
    'py3-linux-i686/pythonw',
]
RENPY_GAME_DIR = 'game'
RENPY_LIB_DIR = 'lib'
RENPY_PY_DIR = 'renpy'
RENPY_TL_DIR = 'tl'
RENPY_DIRS = [
    RENPY_GAME_DIR,
    RENPY_LIB_DIR,
    RENPY_PY_DIR,
]


def try_running(try_fn, except_fn=None, final_fn=None, return_try=True, except_return=False, try_return=True):
    try:
        if return_try:
            return try_fn()
        try_fn()
        return try_return
    except Exception as e:
        logging.exception(e)
        if except_fn is not None:
            except_fn()
        return except_return
    finally:
        if final_fn is not None:
            final_fn()


class ProjzCmdInjection(BaseInjector):
    def __init__(self, project_path: str):
        renpy_init_py = os.path.join(project_path, RENPY_PY_DIR, '__init__.py')
        injection_py = os.path.join(project_path, RENPY_PY_DIR, 'translation', 'projz_injection.py')
        self.pyi = PyCodeInjector(renpy_init_py,
                                  anchor_codes=['import renpy.translation.generation'],
                                  target_codes=['import renpy.translation.projz_injection'], insert_before=True)
        self.fi = PyFileInjector(source_filename=r'resources/codes/projz_injection.py', target_filename=injection_py)

    def __call__(self):
        return self.pyi() and self.fi()

    def undo(self):
        return self.pyi.undo() and self.fi.undo()


def _list_tl_names(project_path: str):
    languages = []
    tl_dir = os.path.join(project_path, RENPY_GAME_DIR, RENPY_TL_DIR)
    items = os.listdir(tl_dir)
    for i in items:
        # we don't need the None dir
        name = file_name(i)
        if exists_dir(os.path.join(tl_dir, name)) and name != 'None':
            languages.append(name)
    print(f'{len(languages)} languages ({languages}) found in {tl_dir}')
    return languages


class ProjzI18nInjection(BaseInjector):
    NOT_FOUND_ERROR_TEXT = """
We couldn't a file named "screens.rpy" in each place of your game dir {ganme_dir} or failed to inject our code.
As a result, you cannot find an i18n button in the Options page of the game. Don't worry, you still 
can show our i18n menu by the shortcut key (Default is Ctrl + i, it can be configured in config.yaml.)

If you want this button, please insert the following code manually at the "Preferences screen" section in screens.rpy:
```python
textbutton _("I18n settings") action Show("projz_i18n_settings")
```
After inserting, this section may like:
```python
## Preferences screen ##########################################################
##
## The preferences screen allows the player to configure the game to better suit
## themselves.
##
## https://www.renpy.org/doc/html/screen_special.html#preferences

screen preferences():

    tag menu

    if renpy.mobile:
        $ cols = 2
    else:
        $ cols = 4

    use game_menu(_("Preferences"), scroll="viewport"):

        vbox:
            textbutton _("I18n settings") action Show("projz_i18n_settings")
            hbox:
                box_wrap True
```
"""
    PROJZ_FONT_DIR = 'projz_fonts'
    ANCHOR_CODE1 = line_strip('''
                hbox:
                    box_wrap True
    
                    if renpy.variant("pc"):
    
                        vbox:
'''.split('\n'))
    ANCHOR_CODE2 = line_strip('''
                    hbox:
                        box_wrap True

                        if renpy.variant("pc") or renpy.variant("web"):

                            vbox:
    '''.split('\n'))
    TARGET_CODE = ['textbutton _("I18n settings") action Show("projz_i18n_settings")']

    def __init__(self, project_path: str, languages: List[str] = None):
        self.project_path = project_path
        self.game_dir = os.path.join(project_path, RENPY_GAME_DIR)
        self.font_dir = os.path.join(self.game_dir, self.PROJZ_FONT_DIR)
        self.enable_console = default_config['renpy']['developer_console']
        self.screen_rpys = walk_and_select(os.path.join(project_path, RENPY_GAME_DIR),
                                           select_fn=lambda x: file_name(x) == 'screens.rpy',
                                           exclude_dirs=[RENPY_TL_DIR])
        self.rpyis = []
        for rpy in self.screen_rpys:
            self.rpyis.append(PyCodeInjector(rpy, anchor_codes=self.ANCHOR_CODE1, target_codes=self.TARGET_CODE,
                                             insert_before=True))
            self.rpyis.append(PyCodeInjector(rpy, anchor_codes=self.ANCHOR_CODE2, target_codes=self.TARGET_CODE,
                                             insert_before=True))

        self.injection_rpy = os.path.join(project_path, RENPY_GAME_DIR, 'projz_i18n_inject.rpy')
        self.inpyi = RpyFileInjector(source_filename=None, target_filename=self.injection_rpy)

        valid_font_map = dict()
        for f in default_config['renpy']['fonts']:
            valid_font_map[file_name(f)] = f

        valid_lang_map = dict()
        lang_map = {i['tl_name']: i for i in default_config['renpy']['lang_map']}
        if languages is None:
            languages = _list_tl_names(project_path)
        for k, v in lang_map.items():
            if k in languages:
                valid_lang_map[k] = v
                valid_font_map[file_name(v['font'])] = v['font']
        print(f'Available languages in i18n menu: {list(valid_lang_map.keys())}')
        print(f'Available fonts in i18n menu: {list(valid_font_map.keys())}')
        self.shortcut_key = default_config['renpy']['i18n_menu']['shortcut_key']
        self.valid_font_map = valid_font_map
        self.valid_lang_map = valid_lang_map
        self.fis = []
        for f, path in self.valid_font_map.items():
            self.fis.append(FileInjector(source_filename=path, target_filename=os.path.join(self.font_dir, f)))

    def __call__(self):
        # inject into screens.rpy
        if len(self.screen_rpys) == 0:
            print(self.NOT_FOUND_ERROR_TEXT.format(ganme_dir=self.game_dir))
        else:
            done = False
            for rpyi in self.rpyis:
                res = rpyi()
                if res:
                    done = True
                    break
            if not done:
                print(self.NOT_FOUND_ERROR_TEXT.format(ganme_dir=self.game_dir))

        with default_read(r'resources/codes/projz_i18n_inject.rpy') as f:
            rpy_template = f.read()
        lang_content = ','.join(
            [f'"{k}":("{v["title"]}","{file_name(v["font"])}")' for k, v in self.valid_lang_map.items()])
        font_content = ','.join(f'"{f}"' for f in self.valid_font_map.keys())
        rpy_template = (rpy_template.replace("{projz_enable_console_content}", str(self.enable_console))
                        .replace("{projz_lang_content}", lang_content)
                        .replace("{projz_shortcut_key}", self.shortcut_key)
                        .replace("{projz_font_content}", font_content))
        # write injection rpy
        with default_write(self.injection_rpy) as f:
            f.write(rpy_template)
        mkdir(self.font_dir)
        # copy fonts into game/proj_fonts
        done = all([f() for f in self.fis])
        return done

    def undo(self):
        res = True
        for rpyi in self.rpyis:
            res = res and rpyi.undo()
        if exists_dir(self.font_dir):
            for f in self.fis:
                res = res and f.undo()
            res = res and self.inpyi.undo()
            try_running(try_fn=lambda: os.rmdir(self.font_dir), return_try=False)
        return res

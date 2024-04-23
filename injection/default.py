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
from injection.base.base import call_chain, undo_chain, BaseChainInjector, UndoOnFailedCallInjector
from injection.base.code import line_strip
from injection.base.file import PyFileInjector, RpyFileInjector, StrFileInjector
from util import walk_and_select, file_name, default_read, mkdir, exists_dir

PYTHON_WIN64_EXE = [
    'windows-x86_64/python.exe',
    'windows-x86_64/pythonw.exe',
    'py2-windows-x86_64/python.exe',
    'py2-windows-x86_64/pythonw.exe',
    'py3-windows-x86_64/python.exe',
    'py3-windows-x86_64/pythonw.exe',
]
PYTHON_WIN32_EXE = [
    'windows-i686/python.exe',
    'windows-i686/pythonw.exe',
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


class ProjzCmdInjection(BaseChainInjector):
    def __init__(self, project_path: str):
        super().__init__()
        renpy_init_py = os.path.join(project_path, RENPY_PY_DIR, '__init__.py')
        injection_py = os.path.join(project_path, RENPY_PY_DIR, 'translation', 'projz_injection.py')
        self.pyi = PyCodeInjector(renpy_init_py,
                                  anchor_codes=['import renpy.translation.generation'],
                                  target_codes=['import renpy.translation.projz_injection'], insert_before=True)
        self.fi = PyFileInjector(source_filename=r'resources/codes/projz_injection.py', target_filename=injection_py)
        self.set_chain([self.pyi, self.fi])


class FontInjection(BaseChainInjector):
    PROJZ_FONT_DIR = 'projz_fonts'

    def __init__(self, project_path, font_list: List[str]):
        super().__init__()
        self.font_dir = os.path.join(project_path, RENPY_GAME_DIR, default_config['renpy']['font']['save_dir'])
        self.valid_font_map = dict()
        if font_list:
            for f in set(font_list):
                self.valid_font_map[file_name(f)] = f
        print(f'Find {len(self.valid_font_map)} fonts: {list(self.valid_font_map.keys())}')
        fis = []
        for f, path in self.valid_font_map.items():
            fis.append(FileInjector(source_filename=path, target_filename=os.path.join(self.font_dir, f)))
        self.set_chain(fis)

    def __call__(self, *args, **kwargs):
        mkdir(self.font_dir)
        return super().__call__(*args, **kwargs)

    def undo(self, *args, **kwargs):
        res = True
        if exists_dir(self.font_dir):
            super().undo(*args, **kwargs)
            try_running(try_fn=lambda: os.rmdir(self.font_dir), return_try=False)
        return res


def _list_tl_names(project_path: str):
    languages = []
    tl_dir = os.path.join(project_path, RENPY_GAME_DIR, RENPY_TL_DIR)
    if exists_dir(tl_dir):
        items = os.listdir(tl_dir)
        for i in items:
            # we don't need the None dir
            name = file_name(i)
            if exists_dir(os.path.join(tl_dir, name)) and name != 'None':
                languages.append(name)
    print(f'{len(languages)} languages ({languages}) found in {tl_dir}')
    return languages


class ProjzI18nInjection(BaseChainInjector):
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
        super().__init__()
        self.project_path = project_path
        self.game_dir = os.path.join(project_path, RENPY_GAME_DIR)
        # I18n button
        self.screen_rpys = walk_and_select(os.path.join(project_path, RENPY_GAME_DIR),
                                           select_fn=lambda x: file_name(x) == 'screens.rpy',
                                           exclude_dirs=[RENPY_TL_DIR])
        self.rpyis = []
        for rpy in self.screen_rpys:
            self.rpyis.append(PyCodeInjector(rpy, anchor_codes=self.ANCHOR_CODE1, target_codes=self.TARGET_CODE,
                                             insert_before=True))
            self.rpyis.append(PyCodeInjector(rpy, anchor_codes=self.ANCHOR_CODE2, target_codes=self.TARGET_CODE,
                                             insert_before=True))

        # Font
        font_list = []
        for f in default_config['renpy']['font']['list']:
            font_list.append(f)
        valid_lang_map = dict()

        # Lang
        lang_map = {i['tl_name']: i for i in default_config['renpy']['lang_map']}
        if languages is None:
            languages = _list_tl_names(project_path)
        simple_languages = []
        for k in languages:
            if k in lang_map:
                v = lang_map[k]
                valid_lang_map[k] = v
                font_list.append(v['font'])
            else:
                simple_languages.append(k)

        # projz_i18n_inject template
        with default_read(r'resources/codes/projz_i18n_inject.rpy') as f:
            rpy_template = f.read()
        lang_content = ','.join(
            [f'"{k}":("{v["title"]}","{file_name(v["font"])}")' for k, v in valid_lang_map.items()])
        slang_content = ','.join([f'"{k}"' for k in simple_languages])
        font_content = ','.join(f'"{file_name(f)}"' for f in set(font_list))
        mconfig = default_config['renpy']
        font_dir = mconfig['font']['save_dir']
        enable_console = mconfig['debug_console']
        enable_developer = mconfig['developer_mode']
        shortcut_key = mconfig['i18n_menu']['shortcut_key']
        rpy_template = (rpy_template
                        .replace("{projz_enable_console_content}", str(enable_console))
                        .replace("{projz_fonts_dir}", str(font_dir))
                        .replace("{projz_enable_developer_content}", str(enable_developer))
                        .replace("{projz_lang_content}", lang_content)
                        .replace("{projz_slang_content}", slang_content)
                        .replace("{projz_shortcut_key}", shortcut_key)
                        .replace("{projz_font_content}", font_content))
        injection_rpy = os.path.join(project_path, RENPY_GAME_DIR, 'projz_i18n_inject.rpy')
        self.inpyi = StrFileInjector(RpyFileInjector(None, target_filename=injection_rpy), rpy_template)
        self.fonts = FontInjection(project_path, font_list)
        self.set_chain(self.rpyis + [self.fonts, self.inpyi])

    def __call__(self, *args, **kwargs):
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

        return call_chain([self.fonts, self.inpyi])


class OnlinePyInjection(BaseInjector):

    def __init__(self, project_path):
        renpy_init_py = os.path.join(project_path, RENPY_PY_DIR, '__init__.py')
        self.import_injection = PyCodeInjector(renpy_init_py,
                                               anchor_codes=['post_import()'],
                                               target_codes=['import renpy.translation.projz_translation'],
                                               insert_before=True)
        injection_py = os.path.join(project_path, RENPY_PY_DIR, 'translation', 'projz_translation.py')
        rconfig = default_config['translator']['realtime']
        with default_read(r'resources/codes/projz_translation.py') as f:
            py_content = f.read()
        py_content = (py_content.replace('{projz_host}', str(rconfig.get('host', '127.0.0.1')).strip())
                      .replace('{projz_port}', str(rconfig.get('port', 8888)).strip())
                      .replace('{projz_retry_time}', str(rconfig.get('retry_time', 10)).strip())
                      .replace('{projz_string_request_time_out}',
                               str(rconfig.get('string_request_time_out', 0.8))).strip()
                      .replace('{projz_dialogue_request_time_out}',
                               str(rconfig.get('dialogue_request_time_out', 1.0))).strip())
        self.code_injection = StrFileInjector(
            PyFileInjector(source_filename=r'resources/codes/projz_translation.py', target_filename=injection_py),
            content=py_content)

    def __call__(self, *args, **kwargs):
        return call_chain([self.import_injection, self.code_injection])

    def undo(self, *args, **kwargs):
        return undo_chain([self.import_injection, self.code_injection])

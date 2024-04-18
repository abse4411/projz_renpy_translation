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

import sys
from typing import Tuple, List

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from qt_material import apply_stylesheet

import qt5.main_ui
from qt5.main_ui import MainWindow
from qt5.ui_config import uconfig
from trans import Translator
from translation_provider.base import Provider, register_provider


class FakeTranslator(Translator):
    def __init__(self, suffix=''):
        self._suffix = suffix

    def translate(self, text: str):
        # time.sleep(1)
        return text + self._suffix


class FakeProvider(Provider):

    def default_api(self) -> str:
        return 'bing'

    def default_source_lang(self) -> str:
        return 'auto'

    def default_target_lang(self) -> str:
        return 'zh-Hans'

    def api_names(self) -> List[str]:
        return ['google', 'bing']

    def languages_of(self, api: str) -> Tuple[List[str], List[str]]:
        langs = ['zh-Hans', 'zh-Hant', 'en', 'jp', 'kr', 'ru', 'fr', 'auto']
        return langs, langs

    def translator_of(self, api: str, source_lang: str, target_lang: str) -> Translator:
        return FakeTranslator(f'({api}:{source_lang}-{target_lang})')


register_provider('Foo', FakeProvider())

# package cmd: pyinstaller -i imgs/proz_icon_simple.ico server_ui.py
if __name__ == "__main__":
    import log
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    qt5.main_ui._theme_xml = uconfig.str_of('theme', 'default_dark.xml')
    apply_stylesheet(app, theme=qt5.main_ui._theme_xml)
    # print(qt_material.list_themes())
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

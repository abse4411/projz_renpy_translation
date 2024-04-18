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
import time
from functools import partial
from queue import Queue

from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTranslator
from PyQt5.QtWidgets import QMainWindow, QDialog, QApplication
from qt_material import QtStyleTools

from local_server.safe import LockObject
from qt5.about import Ui_AboutDialogue
from qt5.lang import get_lang_ts, set_lang
from qt5.main import Ui_MainWindow
from qt5.main_op import loadServerConfig, startServer, undoInjection, injectionGame, selectRenpyDir, startGame, \
    stopServer, applyTranslator, providerChanged, apiChanged, loadFontConfig, writeTranslations, fontChanged, \
    loadGameRootDirs, saveTranslationIndex, errorWrapper, retranslate, transDialogueChanged, transStringChanged, \
    reloadConfig, clearHistory
from qt5.sponsor import Ui_SponsorsDialog
from qt5.ui_config import uconfig
from translation_provider.base import registered_providers

_theme_xml = 'default_dark.xml'


def _set_theme(app: QtStyleTools, xml):
    global _theme_xml
    _theme_xml = xml
    uconfig.put_and_save('theme', _theme_xml)
    app.apply_stylesheet(app, xml)


def setThemeAction(app, obj):
    for k, v in vars(obj).items():
        if k.startswith('actionLight') or k.startswith('actionDark'):
            action_name = v.objectName()
            main = action_name[6:].lower()
            v.triggered.connect(partial(_set_theme, app, f'{main}.xml'))


class AboutWindow(QDialog, QtStyleTools):
    def __init__(self):
        super().__init__()
        self.apply_stylesheet(self, _theme_xml)
        self.main = Ui_AboutDialogue()
        self.main.setupUi(self)


def openAboutDialog():
    d = AboutWindow()
    d.exec()


class SponsorsWindow(QDialog, QtStyleTools):
    def __init__(self):
        super().__init__()
        self.apply_stylesheet(self, _theme_xml)
        self.main = Ui_SponsorsDialog()
        self.main.setupUi(self)


def openSponsorsDialog():
    d = SponsorsWindow()
    d.exec()


# class TextSignal(QObject):
#     textSignal = pyqtSignal(str)
#
#     def write(self, text):
#         self.textSignal.emit(str(text))
#         QApplication.processEvents()
#
#     def flush(self):
#         pass


class OutputWrapper(QObject):
    def __init__(self, parent, queue: Queue, stdout=True):
        super().__init__(parent)
        self._queue = queue
        self._stdout = stdout
        if stdout:
            self._stream = sys.stdout
            sys.stdout = self
        else:
            self._stream = sys.stderr
            sys.stderr = self

    def write(self, text):
        # self._stream.write(text)
        self._queue.put((text, self._stdout))

    def __getattr__(self, name):
        return getattr(self._stream, name)

    def __del__(self):
        try:
            if self._stdout:
                sys.stdout = self._stream
            else:
                sys.stderr = self._stream
        except AttributeError:
            pass


class LogThread(QThread):
    outputWritten = pyqtSignal(object, bool, int)
    cnt = 0
    max_lines = 50

    def __init__(self, queue: Queue):
        super().__init__()
        self._queue = queue
        self.is_running = True

    def run(self):
        while self.is_running:
            if not self._queue.empty():
                text, isStd = self._queue.get()
                self.cnt += 1
                self.outputWritten.emit(text, isStd, self.cnt)
            time.sleep(0.01)

    def stop(self):
        self.is_running = False
        self.wait()


class MainWindow(QMainWindow, QtStyleTools):
    line_count = 0

    def __init__(self):
        super().__init__()
        self.main = Ui_MainWindow()
        self.main.setupUi(self)
        self.index = LockObject()
        self.server = LockObject()
        self.infoThread = None
        self.initThread = None

        # Button state
        self.main.retranslate_button.setDisabled(True)
        self.main.uninject_button.setDisabled(True)
        self.main.startgame_button.setDisabled(True)
        self.main.savetrans_button.setDisabled(True)
        self.main.saveindex_button.setDisabled(True)
        self.main.start_button.setDisabled(True)
        self.main.stop_button.setDisabled(True)
        self.main.translatorapply_button.setDisabled(True)

        # About page
        self.main.actionAbout.triggered.connect(openAboutDialog)
        # Sponsors page
        self.main.actionSponsors.triggered.connect(openSponsorsDialog)

        # Theme
        setThemeAction(self, self.main)

        # Language
        self.trans = QTranslator()
        self.changeLang(get_lang_ts())

        # Log
        # self._std_color = self.main.startgame_button.palette().button().color()
        # self._err_color = Qt.red
        # self.main.log_text.document().setMaximumBlockCount(100)
        # q = Queue()
        # self.logThread = LogThread(q)
        # self.logThread.outputWritten.connect(self.updateLog)
        # self.logThread.start()
        # self.stdout = OutputWrapper(self, q, True)
        # self.stderr = OutputWrapper(self, q, False)

        # self.stdout.outputWritten.connect(self.handleOutput)
        # self.stderr = OutputWrapper(self, False)
        # self.stderr.outputWritten.connect(self.handleOutput)

        # self._stdout = sys.stdout
        # sys.stdout = TextSignal()
        # sys.stdout.textSignal.connect(self.updateStdoutLog)
        #
        # self._stderr = sys.stderr
        # sys.stderr = TextSignal()
        # sys.stderr.textSignal.connect(self.updateStderrLog)

        # Translator
        providers = registered_providers()
        # self.main.translator_combobox.addItems(['bing', 'google'])
        # self.main.sourcelang_combobox.addItems(['auto', 'en'])
        # self.main.targetlang_combobox.addItems(['zh-hans', 'zh-hant'])

        # Server info
        loadServerConfig(self, self.main)
        # Font
        loadFontConfig(self, self.main)
        # Game roots
        loadGameRootDirs(self, self.main)

        # Register actions
        self.main.selectdir_button.clicked.connect(lambda: selectRenpyDir(self, self.main))
        self.main.inject_button.clicked.connect(lambda: injectionGame(self, self.main))
        self.main.uninject_button.clicked.connect(lambda: undoInjection(self, self.main))
        self.main.startgame_button.clicked.connect(lambda: startGame(self, self.main))
        self.main.start_button.clicked.connect(lambda: startServer(self, self.main))
        self.main.stop_button.clicked.connect(lambda: stopServer(self, self.main))
        self.main.translatorapply_button.clicked.connect(lambda: applyTranslator(self, self.main))
        self.main.translator_combobox.currentIndexChanged.connect(lambda: providerChanged(self, self.main))
        self.main.savetrans_button.clicked.connect(lambda: writeTranslations(self, self.main))
        self.main.font_combobox.currentIndexChanged.connect(lambda: fontChanged(self, self.main))
        self.main.saveindex_button.clicked.connect(lambda: saveTranslationIndex(self, self.main))
        self.main.retranslate_button.clicked.connect(lambda: retranslate(self, self.main))
        # self.main.setlogline_button.clicked.connect(lambda: setMaxLogLine(self, self.main))
        # self.main.clearlog_button.clicked.connect(lambda: clearLog(self, self.main))
        self.main.actionEnglish.triggered.connect(lambda: self.changeLang('en'))
        self.main.actionSimplyfied_Chinese.triggered.connect(lambda: self.changeLang('zh-cn'))
        self.main.dialoguetran_check.stateChanged.connect(lambda: transDialogueChanged(self, self.main))
        self.main.stringtran_check.stateChanged.connect(lambda: transStringChanged(self, self.main))
        self.main.actionReloadConfig.triggered.connect(lambda: reloadConfig(self, self.main))
        self.main.clearhistoty_button.clicked.connect(lambda: clearHistory(self, self.main))

        # Select provider
        if providers:
            self.main.translator_combobox.addItems(providers)
            # self.main.translator_combobox.setCurrentIndex(0)
        self.main.api_combobox.currentIndexChanged.connect(lambda: apiChanged(self, self.main))
        errorWrapper(self, lambda: apiChanged(self, self.main))

    # def handleOutput(self, text, stdout):
    #     log_text = self.main.log_text
    #     log_text.moveCursor(QTextCursor.End)
    #     log_text.setTextColor(self._std_color if stdout else self._err_color)
    #     log_text.insertPlainText(text)

    def changeLang(self, lang: str):
        set_lang(lang)
        _app = QApplication.instance()
        self.trans.load(get_lang_ts())
        _app.installTranslator(self.trans)
        self.main.retranslateUi(self)
        uconfig.put_and_save('language', lang)

    def closeEvent(self, event):
        # sys.stderr = self._stderr
        # sys.stdout = self._stdout
        # if hasattr(self, 'stdout'):
        #     del self.stdout
        # if hasattr(self, 'stderr'):
        #     del self.stderr
        # self.logThread.stop()
        event.accept()

    # def updateLog(self, text: str, isStd: bool, cnt: int):
    #     log_text = self.main.log_text
    #     log_text.moveCursor(QTextCursor.End)
    #     log_text.setTextColor(self._std_color if isStd else self._err_color)
    #     log_text.insertPlainText(text)

    # def updateStdoutLog(self, text: str):
    #     log_text_obj = self.main.log_text
    #     # cursor = log_text_obj.textCursor()
    #     # cursor.movePosition(QTextCursor.End)
    #     log_text_obj.append(f'<pre>{text}</pre>')
    #     # log_text_obj.setTextCursor(cursor)
    #     # self.textBrowser.ensureCursorVisible()
    #     # log_text_obj.insertPlainText(text)
    #     # log_text_obj.insertHtml()
    #
    # def updateStderrLog(self, text):
    #     log_text_obj = self.main.log_text
    #     # cursor = log_text_obj.textCursor()
    #     # cursor.movePosition(QTextCursor.End)
    #     # text = text.replace('\n', '<br/>')
    #     log_text_obj.append(f'<span style="color:#e74c3c"><pre>{text}</pre></span>')
    #     # log_text_obj.setTextCursor(cursor)
    #     # self.textBrowser.ensureCursorVisible()
    #     # log_text_obj.insertHtml(f'<span style="color:#e74c3c"><pre>{text}</pre></span><br/>')

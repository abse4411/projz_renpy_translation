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
import logging
import os
import time
from typing import List, Tuple

from PyQt5.QtCore import pyqtSignal, QThread, Qt
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from qt5.ui_config import uconfig
from store import TranslationIndex, index_type
from trans import Translator
from translation_provider.base import get_provider
from config import default_config
from local_server.index import _WebTranslationIndex
from local_server.server import FlaskServer
from qt5.main import Ui_MainWindow
from util import exists_dir, strip_or_none, open_item, exists_file, file_name


def showInfoMsg(app, msg: str, title: str = 'Info'):
    QMessageBox.information(app, title, msg)


def showErrorMsg(app, msg: str, title: str = 'Error'):
    QMessageBox.critical(app, title, msg)


def errorWrapper(app, func, returnRes: bool = True, defaultRes=None):
    try:
        # raise RuntimeError('errorWrapper(app, func, returnRes: bool = True, defaultRes=None):')
        res = func()
        if returnRes:
            return res
    except Exception as e:
        logging.exception(e)
        showErrorMsg(app, str(e))
    return defaultRes


def errorAspect(func):
    def wrapper(app, win: Ui_MainWindow):
        try:
            return func(app, win)
        except Exception as e:
            logging.exception(e)
            showErrorMsg(app, str(e))

    return wrapper


def selectRenpyDir(app, win: Ui_MainWindow):
    options = QFileDialog.Options()
    dirname = QFileDialog.getExistingDirectory(app, "Choose a RenPy game root", options=options)
    if dirname:
        # win.gameroot_combox.addItem()
        win.gameroot_combox.setCurrentText(str(dirname))


@errorAspect
def startGame(app, win: Ui_MainWindow):
    index = app.index.get()
    if index:
        p = index.project
        exe_file = os.path.join(p.project_path, f'{p.project_name}.exe')
        if exists_file(exe_file):
            open_item(exe_file)
        else:
            showErrorMsg(app, f'{exe_file} not found!')
    else:
        win.uninject_button.setDisabled(True)
        showErrorMsg(app, f'Please inject the game first!')


@errorAspect
def undoInjection(app, win: Ui_MainWindow):
    index = app.index.get()
    if index:
        res = errorWrapper(app, lambda: index.undo_injection())
        if res:
            app.index.set(None)
            index.stop()
            updateTextState('Stopped', app, win.translatorstatus_text)
            win.translatorapply_button.setDisabled(True)
            win.uninject_button.setDisabled(True)
            win.savetrans_button.setDisabled(True)
            win.retranslate_button.setDisabled(True)
            win.saveindex_button.setDisabled(True)
            win.inject_button.setEnabled(True)
            win.selectdir_button.setEnabled(True)
            win.gamename_text.setText(None)
            win.gameversion_text.setText(None)
            win.renpyversion_text.setText(None)
            win.gameroot_combox.setDisabled(False)
            win.dialoguenum_text.display(0)
            win.stringnum_text.display(0)
            win.totalnum_text.display(0)
        win.startgame_button.setDisabled(True)
        win.start_button.setDisabled(True)
        showInfoMsg(app, f'Undo injection result: {res}')
    else:
        win.uninject_button.setDisabled(True)
        showErrorMsg(app, f'Please inject the game first!')


@errorAspect
def injectionGame(app, win: Ui_MainWindow):
    if exists_dir(win.gameroot_combox.currentText()):
        launch_text = win.detectgame_btn.isChecked()
        index = errorWrapper(app, lambda: _WebTranslationIndex.from_dir(win.gameroot_combox.currentText(),
                                                                        test_launching=launch_text))
        if index:
            app.index.set(index)
            game_info = index.project.game_info
            win.gamename_text.setText(str(game_info.get('game_name', '')))
            win.gameversion_text.setText(str(game_info.get('game_version', '')))
            win.renpyversion_text.setText(str(game_info.get('renpy_version', '')))
            win.start_button.setEnabled(True)
            win.uninject_button.setEnabled(True)
            win.startgame_button.setEnabled(True)
            win.savetrans_button.setEnabled(True)
            win.retranslate_button.setEnabled(True)
            win.saveindex_button.setEnabled(True)
            win.selectdir_button.setDisabled(True)
            win.inject_button.setDisabled(True)
            win.gameroot_combox.setDisabled(True)
            lend = index.dialogue_size
            lens = index.string_size
            win.dialoguenum_text.display(lend)
            win.stringnum_text.display(lens)
            win.totalnum_text.display(lend + lens)
            font = strip_or_none(win.font_combobox.currentText())
            if font == 'Default':
                font = None
            index.set_font(font)
            showInfoMsg(app, 'Injection succeed!')
            new_dirs = uconfig.list_of('dir_history', [])
            uconfig.put_and_save('dir_history', list(set(new_dirs+[win.gameroot_combox.currentText()])))
        else:
            showInfoMsg(app, 'Injection failed!')
    else:
        showErrorMsg(app, f'{win.gameroot_combox.currentText()} is not a valid dir!')


class CollectServerInfoThread(QThread):
    trigger = pyqtSignal(tuple)

    def __init__(self, server: FlaskServer, index: _WebTranslationIndex):
        super().__init__()
        self._server = server
        self._index = index

    def run(self):
        while True:
            try:
                if not self._server.is_stopped():
                    qs = self._index.query_size
                    ds = self._index.dialogue_size
                    ss = self._index.string_size
                    server_info = {'ok': False if self._server.error else True, 'error': self._server.error}
                    index_info = {'queueing': qs, 'dialogue': ds,
                                  'string': ss, 'total': ds + ss}
                    translator_info = {}
                    err = self._index.error()
                    translator_info['ok'] = False if err else True
                    translator_info['error'] = err
                    self.trigger.emit((server_info, index_info, translator_info))
                else:
                    break
            except Exception as e:
                logging.exception(e)
                break
            time.sleep(1)


def updateTextState(state: str, app, target):
    def _set_color(t, c):
        t.setStyleSheet(f'color: {c}')

    if state == 'Running':
        target.setText(app.tr('Running'))
        _set_color(target, 'green')
    elif state == 'Error':
        target.setText(app.tr('Error'))
        _set_color(target, 'red')
    else:
        target.setText(app.tr(state))
        target.setStyleSheet('')


def _stopServer(app, win: Ui_MainWindow, server: FlaskServer):
    server.stop_server()
    app.server.set(None)
    # app.infoThread.set(None)
    win.start_button.setEnabled(True)
    win.stop_button.setDisabled(True)
    win.uninject_button.setEnabled(True)
    win.translatorapply_button.setDisabled(True)
    updateTextState('Stopped', app, win.serverstatus_text)
    updateTextState('Stopped', app, win.translatorstatus_text)


def _updateServerInfo(app, win: Ui_MainWindow, info):
    server_info, index_info, translator_info = info
    server = app.server.get()
    if server and not server.is_stopped():
        if not server_info['ok']:
            _stopServer(app, win, server)
            logging.exception(server_info['error'])
        else:
            win.queue_text.display(index_info['queueing'])
            win.dialoguenum_text.display(index_info['dialogue'])
            win.stringnum_text.display(index_info['string'])
            win.totalnum_text.display(index_info['total'])
            if not translator_info['ok']:
                updateTextState('Error', app, win.translatorstatus_text)
                showErrorMsg(app, f'Translator is crashed!')
                logging.exception(translator_info['error'])
            # else:
            #     updateTextState('Running', app, win.translatorstatus_text)


@errorAspect
def stopServer(app, win: Ui_MainWindow):
    server = app.server.get()
    if server and not server.is_stopped():
        _stopServer(app, win, server)


@errorAspect
def startServer(app, win: Ui_MainWindow):
    index = app.index.get()
    if index:
        try:
            host = strip_or_none(win.host_text.text())
            port = int(win.port_text.text())
            if host and port:
                server = FlaskServer(index, host, port)
                # server.set_translator(MockTranslator())
                done = server.start_server()
                if done:
                    app.server.set(server)
                    infoThread = CollectServerInfoThread(server, index)
                    infoThread.trigger.connect(lambda x: _updateServerInfo(app, win, x))
                    infoThread.start()
                    app.infoThread = infoThread
                    # app.infoThread.set(infoThread)
                    win.start_button.setDisabled(True)
                    win.stop_button.setEnabled(True)
                    win.uninject_button.setDisabled(True)
                    win.translatorapply_button.setEnabled(True)
                    updateTextState('Running', app, win.serverstatus_text)
                    applyTranslator(app, win)
                else:
                    showErrorMsg(app, f'Launching server failed!')
            else:
                showErrorMsg(app, f'Please set the host and port first!')
        except Exception as e:
            logging.exception(e)
            showErrorMsg(app, f'Initializing server failed!')
    else:
        showErrorMsg(app, f'Please inject the game first!')


@errorAspect
def loadServerConfig(app, win: Ui_MainWindow):
    win.start_button.setDisabled(True)
    try:
        sconfig = default_config['translator']['realtime']
        host = str(sconfig.get('host', '127.0.0.1')).strip()
        port = str(sconfig.get('port', 8888)).strip()
        win.host_text.setText(host)
        win.port_text.setText(port)
        win.start_button.setEnabled(True)
    except Exception as e:
        logging.exception(e)
        showErrorMsg(app, 'Loading server config failed!')


@errorAspect
def loadFontConfig(app, win: Ui_MainWindow):
    win.font_combobox.addItems(['Default'])
    try:
        fconfig = default_config['renpy']['font']
        # print(fconfig)
        font_list = [file_name(f) for f in set(fconfig['list'])]
        win.font_combobox.addItems(font_list)
        default_font = fconfig.get('default', None)
        if default_font and default_font in font_list:
            win.font_combobox.setCurrentText(default_font)
    except Exception as e:
        logging.exception(e)
        showErrorMsg(app, 'Loading font config failed!')


@errorAspect
def apiChanged(app, win: Ui_MainWindow):
    win.sourcelang_combobox.clear()
    win.targetlang_combobox.clear()
    win.translatorapply_button.setDisabled(True)
    # if app.server.get() is None:
    #     return
    provider = get_provider(win.translator_combobox.currentText())
    api = win.api_combobox.currentText()
    error = False
    if api and provider is not None:
        try:
            win.sourcelang_combobox.setEditable(provider.is_source_language_editable())
            win.targetlang_combobox.setEditable(provider.is_target_language_editable())
            slangs, tlangs = provider.languages_of(api)
            if slangs and tlangs:
                dsl = provider.default_source_lang()
                dtl = provider.default_target_lang()
                win.sourcelang_combobox.addItems(slangs)
                win.targetlang_combobox.addItems(tlangs)
                # print(dname, dsl, dtl, slangs)
                if dsl not in slangs:
                    dsl = slangs[0]
                win.sourcelang_combobox.setCurrentIndex(slangs.index(dsl))
                if dtl not in tlangs:
                    dtl = tlangs[-1]
                win.targetlang_combobox.setCurrentIndex(tlangs.index(dtl))
                if app.server.get() is None:
                    return
                win.translatorapply_button.setEnabled(True)
            else:
                error = True
        except Exception as e:
            error = True
            logging.exception(e)
    if error:
        showErrorMsg(app, f'The {api} API of {provider} is crashed!')


@errorAspect
def providerChanged(app, win: Ui_MainWindow):
    win.translatorapply_button.setDisabled(True)
    provider = get_provider(win.translator_combobox.currentText())
    win.api_combobox.setEditable(False)
    win.api_combobox.clear()
    win.sourcelang_combobox.setEditable(False)
    win.targetlang_combobox.setEditable(False)
    win.sourcelang_combobox.clear()
    win.targetlang_combobox.clear()
    error = False
    if provider is not None:
        try:
            names = provider.api_names()
            if names:
                win.api_combobox.setEditable(provider.is_api_editable())
                dname = provider.default_api()
                if dname not in names:
                    dname = names[0]
                win.api_combobox.addItems(names)
                win.api_combobox.setCurrentIndex(names.index(dname))
                if app.server.get() is None:
                    return
                win.translatorapply_button.setEnabled(True)
            else:
                error = True
        except Exception as e:
            error = True
            logging.exception(e)
    if error:
        showErrorMsg(app, f'The {provider} is crashed!')


class InitTranslator(QThread):
    trigger = pyqtSignal(tuple)

    def __init__(self, provider: str, api: str, source: str, target: str, font: str):
        super().__init__()
        self._provider = provider
        self._api = api
        self._source = source
        self._target = target
        self._font = font

    def run(self):
        translator = None
        try:
            provider = get_provider(self._provider)
            if provider:
                translator = provider.translator_of(self._api, self._source, self._target)
        except Exception as e:
            logging.exception(e)
        self.trigger.emit((translator, self._font))


def _updateTranslator(app, win: Ui_MainWindow, data: Tuple[Translator, str]):
    translator, font = data
    try:
        with app.server as server:
            if server and not server.is_stopped():
                if translator is not None:
                    server.set_translator(translator, font)
                    updateTextState('Running', app, win.translatorstatus_text)
                    win.statusbar.showMessage('Applied.', 2000)
                else:
                    showErrorMsg(app, f'Initializing translator failed!')
                win.translatorapply_button.setEnabled(True)
            else:
                win.translatorapply_button.setDisabled(True)
                if translator is not None:
                    translator.close()
                showErrorMsg(app, f'Please make sure that the server is running!')
                updateTextState('Stopped', app, win.translatorstatus_text)
    except Exception as e:
        logging.exception(e)
        showErrorMsg(app, f'Starting translator failed!')


@errorAspect
def applyTranslator(app, win: Ui_MainWindow):
    win.translatorapply_button.setDisabled(True)
    server = app.server.get()
    if server and not server.is_stopped():
        provider = win.translator_combobox.currentText()
        api = win.api_combobox.currentText()
        source = win.sourcelang_combobox.currentText()
        target = win.targetlang_combobox.currentText()
        font = strip_or_none(win.font_combobox.currentText())
        if font == 'Default':
            font = None
        status_str = f'Apply a translator: {provider}/{api}, translation target: {source}->{target}'
        print(status_str)
        win.statusbar.showMessage(status_str, 2000)
        if provider and api and source and target:
            initThread = InitTranslator(provider, api, source, target, font)
            initThread.trigger.connect(lambda x: _updateTranslator(app, win, x))
            initThread.start()
            app.initThread = initThread
        else:
            showErrorMsg(app, f'Invalid translator args!')
    else:
        showErrorMsg(app, f'Please make sure that the server is running!')
        updateTextState('Stopped', app, win.translatorstatus_text)


@errorAspect
def writeTranslations(app, win: Ui_MainWindow):
    win.savetrans_button.setDisabled(True)
    index = app.index.get()
    if index:
        font = strip_or_none(win.font_combobox.currentText())
        if font == 'Default':
            font = None
        index.set_font(font)
        res = errorWrapper(app, index.save_translations)
        if res:
            showInfoMsg(app, 'Save successfully!')
        win.savetrans_button.setEnabled(True)


@errorAspect
def fontChanged(app, win: Ui_MainWindow):
    index = app.index.get()
    if index:
        font = strip_or_none(win.font_combobox.currentText())
        if font == 'Default':
            font = None
        index.set_font(font)


@errorAspect
def saveTranslationIndex(app, win: Ui_MainWindow):
    win.saveindex_button.setDisabled(True)
    index = app.index.get()
    if index:
        try:
            index.save_web_index()
            showInfoMsg(app, 'Save successfully!')
        except Exception as e:
            logging.exception(e)
            showErrorMsg(app, 'Save Failed!')
        win.saveindex_button.setEnabled(True)


@errorAspect
def loadGameRootDirs(app, win: Ui_MainWindow):
    dirs = []
    try:
        dirs.extend(uconfig.list_of('dir_history', []))
    except Exception as e:
        logging.exception(e)
    win.gameroot_combox.addItems(list(set(dirs)))



@errorAspect
def retranslate(app, win: Ui_MainWindow):
    win.retranslate_button.setDisabled(True)
    index = app.index.get()
    if index:
        index.retranslate()
        showInfoMsg(app, 'Retranslation enabled!')
        win.retranslate_button.setEnabled(True)


@errorAspect
def transDialogueChanged(app, win: Ui_MainWindow):
    index = app.index.get()
    if index:
        index.dialogue_translatable(win.dialoguetran_check.isChecked())


@errorAspect
def transStringChanged(app, win: Ui_MainWindow):
    index = app.index.get()
    if index:
        index.string_translatable(win.stringtran_check.isChecked())


@errorAspect
def reloadConfig(app, win: Ui_MainWindow):
    default_config.reload()
    win.statusbar.showMessage('Config file was reloaded.', 2000)

# def clearLog(app, win: Ui_MainWindow):
#     win.log_text.clear()
#
#
# def setMaxLogLine(app, win: Ui_MainWindow):
#     lines = win.maxline_spinbox.value()
#     win.log_text.document().setMaximumBlockCount(lines)

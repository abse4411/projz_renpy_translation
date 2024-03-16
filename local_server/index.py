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
import json
import logging
import os
import threading
import time
from copy import copy
from queue import Queue
from typing import List

from config import default_config
from injection import Project
from injection.base import PyCodeInjector, PyFileInjector
from injection.base.base import UndoOnFailedCallInjector, BaseInjector, undo_chain, call_chain
from injection.base.file import StrFileInjector
from injection.default import RENPY_PY_DIR, FontInjection
from local_server.safe import SafeDict
from translation_provider.base import ApiTranslator
from util import default_read, file_name, exists_dir, mkdir, strip_or_none, exists_file
from util.renpy import list_tags


def _strip_tags(text: str):
    if text:
        tags = list_tags(text)
        if tags:
            for t in tags.keys():
                text = text.replace(t, '')
        return text
    return ''


class TranslationRunner(threading.Thread):
    def __init__(self, translator: ApiTranslator, queue: Queue, update_func,
                 batch_size: int = 1, sleep_time: float = 0.001, daemonic: bool = True):
        threading.Thread.__init__(self)
        self._queue = queue
        self._update_func = update_func
        self._translator = translator
        assert batch_size > 0, f'{batch_size}: batch_size must greater than 0'
        assert sleep_time >= 0.0, f'{batch_size}: sleep_time must not less than 0'
        self._batch_size = batch_size
        self._sleep_time = sleep_time
        self._stop_flag = False
        self._error = None
        super().setDaemon(daemonic)

    def run(self):
        while True:
            if self._stop_flag:
                print('Translator is stopped by the user.')
                return
            packs, texts = [], []
            try:
                while not self._queue.empty():
                    p = self._queue.get()
                    t = p['substituted']
                    packs.append(p)
                    texts.append(_strip_tags(t))
                    if len(packs) == self._batch_size:
                        break
                new_texts = self._translator.translate_batch(texts)
                for p, t in zip(packs, new_texts):
                    p['new_text'] = t
                self._update_func(packs)
            except Exception as e:
                logging.exception(e)
                # reverse get()
                for p in packs:
                    self._queue.put(p)
                self._error = e
                print('Translator is crashed!')
                return
            time.sleep(self._sleep_time)

    def error(self):
        e = self._error
        self._error = None
        return e

    def exit(self):
        self._stop_flag = True


class OnlinePyInjection(BaseInjector):

    def __init__(self, project_path):
        renpy_init_py = os.path.join(project_path, RENPY_PY_DIR, '__init__.py')
        self.import_injection = UndoOnFailedCallInjector(
            PyCodeInjector(renpy_init_py,
                           anchor_codes=['post_import()'],
                           target_codes=['import renpy.translation.projz_translation'],
                           insert_before=True))
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
        self.code_injection = UndoOnFailedCallInjector(StrFileInjector(
            PyFileInjector(
                source_filename=r'resources/codes/projz_translation.py',
                target_filename=injection_py), content=py_content))

    def __call__(self, *args, **kwargs):
        return call_chain([self.import_injection, self.code_injection])

    def undo(self, *args, **kwargs):
        return undo_chain([self.import_injection, self.code_injection])


class WebTranslationIndex:
    SAY_TYPE = 'Say'
    STRING_TYPE = 'String'

    def __init__(self, project: Project, max_queue_size: int = 0):
        self._font = None
        self._project = project
        self._strings = SafeDict()
        # self._strings = dict()
        self._dialogue = SafeDict()
        # self._dialogue = dict()
        self._font_injection = None
        self._code_injection = None
        self._translator = None
        self._queue = Queue(max_queue_size)
        self._runner = None
        self._golobal_ids = set()
        self._set_lock = threading.Lock()
        self._font_dir = default_config['renpy']['font_dir']
        self._wait_time = float(default_config['translator']['realtime'].get('translator_wait_time', 0.5))

    @property
    def project(self):
        return self._project

    @property
    def query_size(self):
        return self._queue.qsize()

    @property
    def dialogue_size(self):
        return len(self._dialogue)

    @property
    def string_size(self):
        return len(self._strings)

    def _add_if_noexisting(self, identifier: str):
        with self._set_lock:
            if identifier not in self._golobal_ids:
                self._golobal_ids.add(identifier)
                return True
            return False

    def has_tid(self, identifier: str):
        with self._set_lock:
            return identifier in self._golobal_ids

    def start(self, **kwargs):
        if self._translator:
            self._runner = TranslationRunner(self._translator, self._queue, self._update_pack, **kwargs)
            self._runner.start()

    def _quote_with_fonttag(self, text):
        if self._font:
            # print(f'{{font={self._font_dir}{self._font}}}{text}{{/font}}')
            return f'{{font={self._font_dir}{self._font}}}{text}{{/font}}'
        return text

    def set_font(self, font: str):
        self._font = strip_or_none(font)

    def set_translator(self, translator: ApiTranslator, font: str = None):
        self._translator = translator
        self._font = strip_or_none(font)

    def _update_string(self, pack: dict):
        # print(f'[Update String]: {pack}')
        # print(self._strings.keys())
        self._strings[pack['identifier']] = pack

    def _update_dialogue(self, pack: dict):
        # print(f'[Update Dialogue]: {pack}')
        # print(self._dialogue.keys())
        self._dialogue[pack['identifier']] = pack

    def update_translation(self, ptype: str, identifier: str, new_text: str):
        if ptype == self.STRING_TYPE:
            p = self._strings.get(identifier)
            if p:
                p['new_text'] = new_text
                self._strings[identifier] = p
        elif ptype == self.SAY_TYPE:
            p = self._dialogue.get(identifier)
            if p:
                p['new_text'] = new_text
                self._dialogue[identifier] = p
        else:
            logging.warning(f'Unknown pack type: {ptype}')

    def _update_pack(self, packs: List[dict]):
        for p in packs:
            t = p['type']
            if t == self.STRING_TYPE:
                self._update_string(p)
            elif t == self.SAY_TYPE:
                self._update_dialogue(p)
            else:
                logging.warning(f'Unknown pack: {p}')

    def translate(self, pack: dict):
        t, tid = pack['type'], pack['identifier']
        # print(f'translate {t}-{tid}: {pack["text"]}')
        p = None
        if self._add_if_noexisting(tid):
            print(f'Miss: {tid}-{pack["text"]}')
            self._queue.put(pack)
            # time.sleep(self._wait_time)
            # if t == self.STRING_TYPE:
            #     p = self._strings.get(tid)
            # elif t == self.SAY_TYPE:
            #     p = self._dialogue.get(tid)
            # # print('p->', p)
            # if p:
            #     print(f'Hit: {tid}-{p["text"]}')
            #     return self._quote_with_fonttag(_strip_tags(p['new_text']))
        else:
            if t == self.STRING_TYPE:
                # print(f'{tid} in _strings={tid in self._strings}')
                # print(self._strings.keys())
                # print(self._strings.get(tid))
                p = self._strings.get(tid)
            elif t == self.SAY_TYPE:
                # print(f'{tid} in _strings={tid in self._dialogue}')
                # print(self._dialogue.keys())
                # print(self._dialogue.get(tid))
                p = self._dialogue.get(tid)
            else:
                print(f'{tid} not Found')
                logging.warning(f'Unknown pack: {pack}')
            if p:
                old_text, new_text = p['substituted'], pack['substituted']
                if old_text != new_text:
                    self._queue.put(pack)
                    return None
                print(f'Hit: {tid}-{p["text"]}')
                return self._quote_with_fonttag(_strip_tags(p['new_text']))
        return None

    def stop(self):
        if self._runner:
            self._runner.exit()

    def error(self):
        if self._runner:
            return self._runner.error()
        return None

    def undo_injection(self):
        res = undo_chain([self._font_injection, self._code_injection])
        return res

    def save_translations(self):
        save_json = os.path.join(self._project.project_path, 'projz_translations.json')
        print(f'Writing translations to: {save_json}')
        s = self._strings.copy()
        d = self._dialogue.copy()
        new_s, new_d = dict(), dict()
        for k, v in s.items():
            new_v = copy(v)
            new_v['new_text'] = self._quote_with_fonttag(_strip_tags(new_v['new_text']))
            new_s[k] = new_v
        for k, v in d.items():
            new_v = copy(v)
            new_v['new_text'] = self._quote_with_fonttag(_strip_tags(new_v['new_text']))
            new_d[k] = new_v
        with open(save_json, 'w', encoding='utf-8') as f:
            json.dump({'String': new_s, 'Say': new_d}, f, ensure_ascii=False, indent=2)
        print(f'Translations stored: {len(s)} dialogue translations, {len(d)} string translations')
        return True

    @classmethod
    def from_dir(cls, project_path: str, default_tl_dir: str = None):
        print('Injecting translation code...')
        code_injection = UndoOnFailedCallInjector(OnlinePyInjection(project_path))
        font_injection = UndoOnFailedCallInjector(FontInjection(project_path, default_config['renpy']['fonts']))
        chain = [font_injection, code_injection]
        p = Project.from_dir(project_path, test=True, injections=chain)
        if p:
            index = cls(p)
            # if call_chain(chain):
            print('Done!')
            index._font_injection = font_injection
            index._code_injection = code_injection
            try:
                save_json = os.path.join(project_path, 'projz_translations.json')
                if exists_file(save_json):
                    print(f'Loading stored translations from: {save_json}')
                    with open(save_json, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    s = json_data.get('String', {})
                    d = json_data.get('Say', {})
                    index._strings.update(s)
                    index._dialogue.update(d)
                    for tid in s.keys():
                        index._golobal_ids.add(tid)
                    for tid in d.keys():
                        index._golobal_ids.add(tid)
                    print(f'Translations updated: {len(index._dialogue)} dialogue translations, '
                          f'{len(index._strings)} string translations')
            except Exception as e:
                logging.exception(e)
            return index
        else:
            print('Failed!')
            undo_chain(chain)
        return None
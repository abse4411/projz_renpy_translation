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
import re
import threading
import time
from copy import copy
from queue import Queue
from typing import List

from config import default_config
from injection import Project
from injection.base.base import UndoOnFailedCallInjector, undo_chain
from injection.default import FontInjection, OnlinePyInjection
from local_server.safe import SafeDict
from store.misc import quote_with_fonttag
from store.web_index import WebTranslationIndex
from trans import Translator
from util import strip_or_none, exists_file
from util.renpy import strip_tags, is_translatable


class TranslationRunner(threading.Thread):
    def __init__(self, translator: Translator, queue: Queue, update_func,
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

    def _close_translator(self):
        try:
            print('Release resources of the translator...')
            self._translator.close()
        except Exception as e:
            logging.exception(e)

    def run(self):
        while True:
            if self._stop_flag:
                self._close_translator()
                print('Translator is stopped by the user.')
                return
            packs, texts, passed_packs = [], [], []
            try:
                while not self._queue.empty():
                    p = self._queue.get()
                    t = p['substituted']
                    s_text = strip_tags(t)
                    if strip_or_none(s_text) is not None and is_translatable(s_text):
                        texts.append(s_text)
                        packs.append(p)
                    else:
                        p['new_text'] = t
                        passed_packs.append(p)
                    if len(packs) == self._batch_size:
                        break
                self._update_func(passed_packs)
                new_texts = self._translator.translate_batch(texts)
                for p, t in zip(packs, new_texts):
                    p['new_text'] = t
                self._update_func(packs)
            except Exception as e:
                logging.exception(e)
                self._close_translator()
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


class _WebTranslationIndex:
    SAY_TYPE = 'Say'
    STRING_TYPE = 'String'

    def __init__(self, project: Project, max_queue_size: int = 0):
        self._fdict = None
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
        self._font_dir = default_config['renpy']['font']['save_dir']
        self._wait_time = float(default_config['translator']['realtime'].get('translator_wait_time', 0.5))
        self._tran_string = False
        self._tran_dialogue = True

    def string_translatable(self, enable: bool):
        self._tran_string = enable

    def dialogue_translatable(self, enable: bool):
        self._tran_dialogue = enable

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
        return quote_with_fonttag(self._font_dir, self._font, text)

    def set_font(self, font: str):
        self._font = strip_or_none(font)

    def set_translator(self, translator: Translator, font: str = None):
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

    def should_translate(self, text:str):
        res = True
        if self._fdict:
            if self._fdict['regex']:
                if self._fdict['regex'].search(text):
                    res = False
            else:
                if self._fdict['match_case']:
                    if self._fdict['text'] in text:
                        res = False
                else:
                    text = text.lower()
                    if self._fdict['text'] in text:
                        res = False
            if self._fdict['converse']:
                res = not res
        return res

    def translate(self, pack: dict) -> str:
        t, tid, text = pack['type'], pack['identifier'], pack['text']
        print(pack)
        # print(f'translate {t}-{tid}: {pack["text"]}')
        if t == self.STRING_TYPE:
            if not self._tran_string:
                return None
        elif t == self.SAY_TYPE:
            if not self._tran_dialogue:
                return None
        else:
            logging.warning(f'Unknown ~~ pack: {pack}')
        if not self.should_translate(pack['substituted']):
            print(f'Ignore: {pack["substituted"]}')
            return None
        p = None
        if self._add_if_noexisting(tid):
            print(f'Miss: {tid}-{text}')
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
                return self._quote_with_fonttag(strip_tags(p['new_text']))
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

    def retranslate(self):
        with self._set_lock:
            self._golobal_ids.clear()

    def set_filter(self, fdict:dict):
        if fdict['regex']:
            if fdict['match_case']:
                regex = re.compile(fdict['text'])
            else:
                regex = re.compile(fdict['text'], re.IGNORECASE)
            fdict['regex'] = regex
        else:
            fdict['regex'] = False
            if not fdict['match_case']:
                fdict['text'] = fdict['text'].lower()
        self._fdict = fdict

    def clear_filter(self):
        self._fdict = None

    def empty_queue(self):
        while not self._queue.empty():
            self._queue.get()

    def empty_strings(self):
        with self._set_lock:
            self._strings.clear()

    def empty_dialogue(self):
        with self._set_lock:
            self._dialogue.clear()

    def save_translations(self):
        save_json = os.path.join(self._project.project_path, 'projz_translations.json')
        print(f'Writing translations to: {save_json}')
        s = self._strings.copy()
        d = self._dialogue.copy()
        new_s, new_d = dict(), dict()
        for k, v in s.items():
            new_v = copy(v)
            new_v['new_text'] = self._quote_with_fonttag(strip_tags(new_v['new_text']))
            new_s[k] = new_v
        for k, v in d.items():
            new_v = copy(v)
            new_v['new_text'] = self._quote_with_fonttag(strip_tags(new_v['new_text']))
            new_d[k] = new_v
        with open(save_json, 'w', encoding='utf-8') as f:
            json.dump({'String': new_s, 'Say': new_d}, f, ensure_ascii=False, indent=2)
        print(f'Translations stored: {len(s)} dialogue translations, {len(d)} string translations')
        return True

    def save_web_index(self, nickname: str = None, tag: str = None, lang: str = 'None'):
        s = self._strings.copy()
        d = self._dialogue.copy()
        return WebTranslationIndex.from_data(self.project, {'String': s, 'Say': d}, nickname, tag, self._font, lang)

    @classmethod
    def from_dir(cls, project_path: str, test_launching: bool = True, default_tl_dir: str = None):
        print('Injecting translation code...')
        code_injection = UndoOnFailedCallInjector(OnlinePyInjection(project_path))
        font_injection = UndoOnFailedCallInjector(FontInjection(project_path, default_config['renpy']['font']['list']))
        project_chain = [('Font', font_injection), ('Web', code_injection)]
        chain = [i[1] for i in project_chain]
        p = Project.from_dir(project_path, test=test_launching, injections=project_chain)
        if p:
            index = cls(p)
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

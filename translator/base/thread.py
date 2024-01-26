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
import threading
import time
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple

import tqdm

from config.base import ProjzConfig
from .template import TranslatorTemplate
from util import yes


class _translator_counter(TranslatorTemplate):
    def __init__(self, count_on_batch: bool):
        super().__init__()
        self._translator = None
        self._count_on_batch = count_on_batch
        self.cnt = 0

    def set_translator(self, translator: TranslatorTemplate):
        self._translator = translator
        self._translate_batch = translator.translate_batch
        self._translate = translator.translate

        def translate_wrapper(text: str):
            res = self._translate(text)
            self.cnt += 1
            return res

        def translate_batch_wrapper(texts: List[str]):
            res = self._translate_batch(texts)
            self.cnt += len(res)
            return res

        if self._count_on_batch:
            translator.translate_batch = translate_batch_wrapper
        else:
            translator.translate = translate_wrapper

    def do_init(self, args, config: ProjzConfig):
        self._translator.do_init(args, config)

    def invoke(self, tids_and_text: List[Tuple[str, str]], update_func):
        self._translator.invoke(tids_and_text, update_func)


class TranslationTaskRunner:
    def __init__(self, args, config: ProjzConfig, template_cls, limit: int, num_workers: int,
                 count_on_batch: bool, wait_for_init=True, wait_prompt: str = None):
        self._args = args
        self._config = config
        self._template_cls = template_cls
        self._limit = limit
        self._num_workers = num_workers
        self._count_on_batch = count_on_batch
        self._wait_for_init = wait_for_init
        self._wait_prompt = wait_prompt

    def _inner_update(self, tids_and_text: List[Tuple[str, str]]):
        try:
            self._lock.acquire()
            self._update_func(tids_and_text)
        except Exception as e:
            print(f'error: {e}')
            logging.exception(e)
        finally:
            self._lock.release()

    def translation_task(self, counter: _translator_counter, tids_and_text: List[Tuple[str, str]]):
        tid = threading.current_thread().ident
        translator = None
        try:
            translator = self._template_cls()
            counter.set_translator(translator)
            print(f'[{tid}] Initing the web translator.')
            translator.do_init(self._args, self._config)
        except Exception as e:
            print(f'[{tid}] Error: {e}.')
            logging.exception(e)
            if translator is not None:
                translator.close()
            return
        finally:
            if self._wait_flag:
                self._sem.release()
        self._event.wait()
        if self._stop_flag:
            print(f'[{tid}] Stopped by user.')
            return
        try:
            counter.invoke(tids_and_text, self._inner_update)
        except Exception as e:
            print(f'[{tid}] Error: {e}.')
            logging.exception(e)
            translator.close()

    def invoke(self, tids_and_text: List[Tuple[str, str]], update_func):
        self._update_func = update_func
        # Distribute untranslated texts to translators
        n_texts = len(tids_and_text)
        if self._args.limit >= 0:
            n_texts = self._args.limit
            print(f'The max number of lines is set to {n_texts}.')
        if n_texts <= 0:
            print('No untranslated lines to translate.')
            return
        batches = []
        batch_size = max(n_texts // self._args.num_workers + 2, 1)
        if batch_size == 1:
            batches.append(tids_and_text)
        else:
            for i in range(0, n_texts, batch_size):
                batches.append(tids_and_text[i: min(i + batch_size, n_texts)])

        true_num_worker = len(batches)
        print(f'Dispatching {true_num_worker} worker(s) with batch size = {batch_size}')

        # do_init for translators
        threads = []
        counters = []
        self._event = threading.Event()
        self._event.clear()
        self._lock = threading.Lock()
        self._sem = threading.BoundedSemaphore(true_num_worker)
        self._wait_flag = self._wait_for_init
        self._stop_flag = False
        executor = ThreadPoolExecutor(max_workers=self._num_workers)
        for b in batches:
            if self._wait_for_init:
                self._sem.acquire()
            counter = _translator_counter(self._count_on_batch)
            counters.append(counter)
            threads.append(executor.submit(self.translation_task, counter, b))

        def _all_done(ts):
            for t in ts:
                if not t.done():
                    return False
            return True

        if self._wait_for_init:
            for i in range(len(batches)):
                self._sem.acquire()
            print(self._wait_prompt)

        if not _all_done(threads) and yes('Do you want to start translating?'):
            last_cnt = 0
            pbar = tqdm.tqdm(total=n_texts, desc=f'Translating')

            self._event.set()
            while not _all_done(threads):
                time.sleep(1)
                cnt = sum([c.cnt for c in counters])
                if cnt > last_cnt:
                    pbar.update(cnt - last_cnt)
                    last_cnt = cnt
            print('Translation tasks completed.')
        else:
            self._stop_flag = True
            self._event.set()
            print('Translation tasks canceled.')
        executor.shutdown()


class ConcurrentTranslatorTemplate(TranslatorTemplate):
    def __init__(self):
        super().__init__()
        self._taskrunner = None

    def register_args(self, parser: ArgumentParser):
        super().register_args(parser)
        parser.add_argument('--limit', type=int, default=-1,
                            help='The max number of lines to be translated. Negative values mean no limit.')
        parser.add_argument('-nw', '--num_workers', type=int, default=1,
                            help='The number of web translator instances to use. Larger value can improve the'
                                 'translation speed but use more resources (of CPU and Memory).')

    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)
        max_workers = config['translator']['max_workers']
        assert args.num_workers >= 1, 'The min value of --num_workers should be greater than 0!'
        assert args.num_workers <= max_workers, f'The --num_workers should be not greater that {max_workers}'
        self._taskrunner = None

    def create_taskrunner(self, template_cls, count_on_batch: bool,
                          wait_for_init=True, wait_prompt: str = None):
        self._taskrunner = TranslationTaskRunner(self.args, self.config, template_cls,
                                                 self.args.limit, self.args.num_workers,
                                                 count_on_batch, wait_for_init, wait_prompt)

    def invoke(self, tids_and_text: List[Tuple[str, str]], update_func):
        assert self._taskrunner is not None, f'Please call the create_taskrunner() before calling invoke()'
        self._taskrunner.invoke(tids_and_text, update_func)

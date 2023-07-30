import logging
import os.path
import threading
import time
from typing import List

import numpy as np
import tqdm
from past.builtins import raw_input

from config.config import default_config

from concurrent.futures import ThreadPoolExecutor

from store.index import project_index
from util.misc import my_input


class concurrent_translator:
    def __init__(self, proj: project_index, translator_class):
        self.num_workers = default_config.num_workers
        self.translator_class = translator_class
        self.executor = ThreadPoolExecutor(max_workers=default_config.num_workers)
        self.proj = proj

    def safe_update(self, sources: List[str], targets: List[str]):
        self.lock.acquire()
        self.proj.update(sources, targets)
        self.pbar.update(len(sources))
        self.lock.release()

    def translate(self, untranslated_lines):
        try:
            logging.info(f'Thread {threading.get_ident()}: Starting the web translator...')
            web_translator = self.translator_class()
        except Exception as e:
            logging.error(
                f'Thread {threading.get_ident()}: Error in starting the web translator, {len(untranslated_lines)} untranslated line(s) will be not translated: {e}')
            return
        finally:
            self.sem.release()
        logging.info(f'Thread {threading.get_ident()}: Waiting for user input...')
        self.event.wait()
        if self.quit:
            logging.info(f'Thread {threading.get_ident()}: Stopped by user')
            return
        sources, targets = [], []
        try:
            logging.info(
                f'Thread {threading.get_ident()}: Starting translating {len(untranslated_lines)} untranslated line(s)')
            for line in untranslated_lines:
                new_text = web_translator.translate(line)
                if new_text is None:
                    logging.warning(f'Thread {threading.get_ident()}: Error in translating {line}, it will ignored!')
                    continue
                sources.append(line)
                targets.append('@@' + new_text)
                if len(sources) > 20:
                    self.safe_update(sources, targets)
                    sources, targets = [], []
            if len(sources) > 0:
                self.safe_update(sources, targets)
        except Exception as e:
            logging.error(f'Thread {threading.get_ident()}: Error during translating: {e}')
        pass

    def start(self):
        if self.proj.untranslation_size <= 0:
            logging.info(f'All texts in {self.proj.full_name} are translated!')
            return
        untranslated_lines = self.proj.untranslated_lines
        batches = []
        batch_size = max(len(untranslated_lines) // self.num_workers, 1)
        if batch_size == 1:
            batches = [[untranslated_lines]]
        else:
            for i in range(0, len(untranslated_lines), batch_size):
                batches.append(untranslated_lines[i: min(i + batch_size, len(untranslated_lines))])

        self.event = threading.Event()
        self.sem = threading.BoundedSemaphore(len(batches))
        self.lock = threading.Lock()
        self.quit = False
        threads = []
        for b in batches:
            self.sem.acquire()
            threads.append(self.executor.submit(self.translate, b))
        logging.info('Waiting for all threads...')
        self.sem.acquire()
        self.sem.release()
        print('Now you can do any operation on these opened browsers, like setting your translation setting: English -> Chinese.')
        while True:
            yes = my_input('After all, enter Y/y to start, or Q/q to exit:')
            yes = yes.strip().lower()
            if yes == 'y':
                break
            elif yes == 'q':
                self.quit = True
                break
        self.pbar = tqdm.tqdm(total=len(untranslated_lines), desc=f'Translating')
        self.event.set()
        if yes == 'y':
            def _all_done(ts):
                for t in ts:
                    if not t.done():
                        return False
                return True

            while not _all_done(threads):
                time.sleep(10)
                self.lock.acquire()
                # Saving every 10s
                self.proj.save_by_default()
                self.lock.release()
            self.proj.save_by_default()
        self.pbar.close()


class google_translator:
    def translate(self, text):
        # time.sleep(0.01)
        return f"[{text}] is translated!"


if __name__ == '__main__':
    import log.logger
    p = project_index.load_from_file(os.path.join(default_config.project_path, f'spclass_V0.1.7a.pt'))
    c = concurrent_translator(p, google_translator)
    c.start()
    p.apply_by_default()
    pass

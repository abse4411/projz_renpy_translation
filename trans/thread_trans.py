import logging
import os.path
import threading
import time
from typing import List, Tuple

import numpy as np
import tqdm

from config.config import default_config

from concurrent.futures import ThreadPoolExecutor

from store.index import project_index
from util.misc import my_input, var_list, strip_tags, strip_breaks


class concurrent_translator:
    def __init__(self, proj: project_index, translator_class):
        self.num_workers = default_config.num_workers
        self.translator_class = translator_class
        self.executor = ThreadPoolExecutor(max_workers=default_config.num_workers)
        self.proj = proj

    def safe_update(self,translated_lines: List[Tuple[str, str]], lang:str):
        self.lock.acquire()
        try:
            self.proj.update(translated_lines, lang)
            self.pbar.update(len(translated_lines))
        except Exception as e:
            logging.exception(e)
        finally:
            self.lock.release()

    def translate(self, untranslated_lines: List[Tuple[str, str]], lang:str):
        try:
            logging.info(f'Starting the web translator...')
            web_translator = self.translator_class()
        except Exception as e:
            logging.error(
                f'Error in starting the web translator, {len(untranslated_lines)} untranslated line(s) will be not translated: {e}')
            return
        finally:
            self.sem.release()
        logging.info(f'Waiting for user input...')
        self.event.wait()
        if self.quit:
            logging.info(f'Stopped by user')
            web_translator.close()
            return
        translated_lines = []
        try:
            logging.info(
                f'Starting translating {len(untranslated_lines)} untranslated line(s)')
            last_output_text = None
            for tid, line in untranslated_lines:
                if line.strip() == '':
                    logging.warning(f'Empty text [{line}] found!')
                    translated_lines.append((tid, line))
                    continue
                raw_line = line
                line = strip_tags(line)
                renpy_vars = var_list(line)
                # replace the var by another name
                tvar_list = [f'T{i}' for i in range(len(renpy_vars))]
                t_line = line
                for i in range(len(tvar_list)):
                    t_line = t_line.replace(renpy_vars[i], tvar_list[i])
                new_text = web_translator.translate(t_line)
                if new_text is None:
                    logging.warning(f'Error in translating [{raw_line}], it will ignored!')
                    continue
                if new_text == last_output_text:
                    logging.warning(f'Error in translating [{raw_line}] (The translated text ({new_text}) is the same as the last translated text), it will ignored!')
                    continue
                last_output_text = new_text
                new_text = strip_breaks(new_text)
                # convert the var back
                for i in range(len(tvar_list)):
                    new_text = new_text.replace(tvar_list[i], renpy_vars[i])

                translated_lines.append((tid, '@@' + new_text))
                if len(translated_lines) > 20:
                    self.safe_update(translated_lines, lang)
                    translated_lines = []
            if len(translated_lines) > 0:
                self.safe_update(translated_lines, lang)
        except Exception as e:
            logging.error(f'Error occurred during translating [{e}], this thread is going to exit!')
        finally:
            web_translator.close()

    def start(self, lang:str):
        if self.proj.untranslation_size(lang) <= 0:
            logging.info(f'All texts in {self.proj.full_name} of language {lang} are translated!')
            return
        untranslated_lines = self.proj.untranslated_lines(lang)
        batches = []
        batch_size = max((len(untranslated_lines)+1) // self.num_workers, 1)
        if batch_size == 1:
            batches = [[untranslated_lines]]
        else:
            for i in range(0, len(untranslated_lines), batch_size):
                batches.append(untranslated_lines[i: min(i + batch_size, len(untranslated_lines))])
        logging.info(f'Dispatching {len(batches)} worker(s) with batch size {batch_size}')
        self.event = threading.Event()
        self.event.clear()
        self.sem = threading.BoundedSemaphore(len(batches))
        self.lock = threading.Lock()
        self.quit = False
        threads = []
        for b in batches:
            self.sem.acquire()
            threads.append(self.executor.submit(self.translate, b, lang))
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
                try:
                    # Saving every 10s
                    self.proj.save_by_default()
                except Exception as e:
                    logging.error(f'Error during Saving: {e}')
                finally:
                    self.lock.release()
            try:
                self.proj.save_by_default()
            except Exception as e:
                logging.error(f'Error during Saving: {e}')
            finally:
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

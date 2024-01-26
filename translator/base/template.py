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
from argparse import ArgumentParser
from typing import Tuple, List

from config.base import ProjzConfig
from store.database.base import flush
from translator.base import Translator


class TranslatorTemplate(Translator):

    def __init__(self):
        super().__init__()
        self.config = None
        self.args = None

    def register_args(self, parser: ArgumentParser):
        pass

    def do_init(self, args, config: ProjzConfig):
        self.args = args
        self.config = config

    def close(self):
        pass

    def invoke(self, tids_and_text: List[Tuple[str, str]], update_func):
        texts = [t[1] for t in tids_and_text]
        tids = [t[0] for t in tids_and_text]
        new_texts = self.translate_batch(texts)
        if len(new_texts) != len(texts):
            print(f'Returned translated texts are expected with size of {len(texts)}, but got {len(new_texts)}')
        new_tid_and_text = list(zip(tids, new_texts))
        update_func(new_tid_and_text)
        self.close()  # close for the subclass


class CachedTranslatorTemplate(TranslatorTemplate):
    def __init__(self):
        super().__init__()
        self._cache_size = None

    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)
        cache_size = config['translator']['write_cache_size']
        if cache_size < 100:
            logging.warning(f'Low write_cache_size({cache_size}) means more frequent disk I/O operations,'
                            f' it may cause a high system load.')
        self._cache_size = max(cache_size, 100)

    def invoke(self, tids_and_text: List[Tuple[str, str]], update_func):
        texts = [t[1] for t in tids_and_text]
        tids = [t[0] for t in tids_and_text]
        n_texts = len(tids_and_text)
        for i in range(0, n_texts, self._cache_size):
            end_dix = min(i + self._cache_size, n_texts)
            # print(i, end_dix, n_texts)
            batch_tids = tids[i:end_dix]
            batch_texts = texts[i:end_dix]
            new_texts = self.translate_batch(batch_texts)
            if len(new_texts) != len(batch_texts):
                print(
                    f'Returned translated texts are expected with size of {len(batch_texts)}, but got {len(new_texts)}')
                continue
            new_tid_and_text = list(zip(batch_tids, new_texts))
            update_func(new_tid_and_text)
            print('Flushing...')
            flush()
        self.close()  # close for the subclass

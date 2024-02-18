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
from argparse import ArgumentParser
from typing import List, Tuple

import torch.cuda
from prettytable import PrettyTable

from command.translation.base import register_cmd_translator
from config.base import ProjzConfig
from translator.base import CachedTranslatorTemplate
from util import exists_dir, strip_or_none, my_input, line_to_args
import dl_translate as dlt

AVAILABLE_MODELS = ['m2m100', 'mbart50', 'nllb200']


class DlTranslator(CachedTranslatorTemplate):
    def __init__(self):
        super().__init__()
        self._batch_size = None
        self._target = None
        self._source = None
        self._model_path = None
        self._model_name = None

    def register_args(self, parser: ArgumentParser):
        super().register_args(parser)
        parser.add_argument('-n', '--name', choices=AVAILABLE_MODELS, default='mbart50',
                            help='The name of deep learning translation model.')
        parser.add_argument('-b', '--batch_size', type=int, default=4,
                            help='The batch size for translating. Lager value may bring faster translation speed '
                                 'but consumes more GPU memory')

    def _load_model(self):
        print(f'Start loading the {self._model_name} model')
        st_time = time.time()
        if self._model_path:
            model_path = os.path.join(self._model_path, self._model_name)
            assert exists_dir(model_path), f'Invalid model path: {model_path}'
            print(f'Loading the model from: {model_path}')
            self.mt = dlt.TranslationModel(model_path, model_family=self._model_name)
        else:
            self.mt = dlt.TranslationModel(self._model_name)
        print(f'The model is loaded in {time.time() - st_time:.1f}s')

    def determine_translation_target(self):
        ava_langs = sorted(list(self.mt.available_languages()))
        ava_indexes = list(range(len(ava_langs)))

        cols = 4
        rows = [['Index', 'Language'] * cols]
        tmp_row = []
        for i, l in enumerate(ava_langs):
            tmp_row.append(f'{i}')
            tmp_row.append(l)
            if len(tmp_row) % (cols * 2) == 0:
                rows.append(tmp_row)
                tmp_row = []
        if len(tmp_row) != 0:
            fillers = [''] * (cols * 2 - len(tmp_row))
            rows.append(tmp_row + fillers)
        table = PrettyTable(header=False)
        for r in rows:
            table.add_row(r)
        while True:
            print(table)
            args = my_input(
                'Please set the translation target (enter two language indexes from above table, '
                'like "0 1" which means that translating text from '
                f'source language {ava_langs[0]} into target language {ava_langs[1]}), or enter Q/q to exit): ')
            args = line_to_args(args.strip())
            if len(args) >= 1:
                if len(args) == 1:
                    if args[0].lower() == 'q':
                        return False
                if len(args) == 2:
                    try:
                        s, t = int(args[0]), int(args[1])
                        assert s in ava_indexes and t in ava_indexes, f'{s} or {t} is out of range!'
                        self._source = ava_langs[s]
                        self._target = ava_langs[t]
                        return True
                    except Exception as e:
                        logging.exception(e)

    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)
        assert args.batch_size > 0, f'The batch_size must be greater than 0!'
        self._batch_size = args.batch_size
        self._model_path = strip_or_none(config['translator']['ai']['model_path'])
        self._model_name = args.name
        self._load_model()

    def invoke(self, tids_and_text: List[Tuple[str, str]], update_func):
        done = self.determine_translation_target()
        if done:
            super().invoke(tids_and_text, update_func)
            print('Translation tasks completed.')
        else:
            print('Translation tasks canceled.')

    def close(self):
        del self.mt
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def translate(self, text: str):
        return self.mt.translate(text, self._source, self._source, batch_size=1, verbose=True)

    def translate_batch(self, texts: List[str]):
        return self.mt.translate(texts, self._source, self._source, batch_size=self._batch_size, verbose=True)


register_cmd_translator('ai', DlTranslator)

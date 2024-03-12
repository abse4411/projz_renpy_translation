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
from typing import List

import tqdm
from prettytable import PrettyTable

from command.translation.base import register_cmd_translator
from config.base import ProjzConfig
from translator.base import CachedTranslatorTemplate
from util import my_input, line_to_args

ts = None
_preacceleration_done = False


class TranslatorsLibTranslator(CachedTranslatorTemplate):
    def __init__(self):
        super().__init__()
        self.trans_kwargs = None
        self.translator = None
        self._source = None
        self._target = None

    def register_args(self, parser: ArgumentParser):
        super().register_args(parser)
        global ts
        import translators as ts
        parser.add_argument('-n', '--name', choices=ts.translators_pool, default='bing',
                            help='The name of translation services.')
        parser.add_argument("-a", "--auto", action='store_true',
                            help="Load translation settings form config.")

    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)
        tconfig = self.config['translator']['translators']
        self.trans_kwargs = tconfig.get('translate_text', {})
        self.trans_kwargs.pop('query_text', None)
        self.trans_kwargs.pop('translator', None)
        self.trans_kwargs.pop('from_language', None)
        self.trans_kwargs.pop('to_language', None)
        use_preacceleration = self.trans_kwargs.pop('if_use_preacceleration', False)
        kwargs = tconfig.get('preaccelerate', {})
        global _preacceleration_done
        if use_preacceleration and not _preacceleration_done:
            from translators.server import preaccelerate
            _ = preaccelerate(kwargs)
            _preacceleration_done = True
        if self.args.auto:
            self.translator = tconfig['api_name']
            self._source = tconfig['from_language']
            self._target = tconfig['to_language']
            print('Using config from config.yaml:')
            print(f'translation service: {self.translator}')
            print(f'from_language: {self._source}')
            print(f'to_language: {self._target}')
            return True
        self.translator = args.name
        return self.determine_translation_target()

    def determine_translation_target(self):
        ava_langs = sorted(list(ts.get_languages(self.translator).keys())) + ['auto']
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
            print('The "auto" is only for the source language!')
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

    def translate(self, text: str):
        res = ts.translate_text(text, from_language=self._source, to_language=self._target,
                                translator=self.translator, **self.trans_kwargs)
        # print(res)
        return res

    def translate_batch(self, texts: List[str]):
        new_text = []
        for t in tqdm.tqdm(texts, desc='Translating'):
            new_text.append(self.translate(t))
        return new_text


register_cmd_translator('ts', TranslatorsLibTranslator)

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
from argparse import ArgumentParser
from typing import List

from command.translation.base import register_cmd_translator
from config.base import ProjzConfig
from trans.openai_api import OpenAITranslator
from translator.base import CachedTranslatorTemplate
from util import strip_or_none, my_input, line_to_args
from util.translate import BatchTranslator


class OpenAILibTranslator(CachedTranslatorTemplate):
    def __init__(self):
        super().__init__()
        self._model = None
        self.trans_kwargs = None
        self.translator = None
        self._target = None
        self._open_ai = None

    def register_args(self, parser: ArgumentParser):
        super().register_args(parser)
        parser.add_argument("-a", "--auto", action='store_true',
                            help="Load translation settings form config.")

    def determine_translation_target(self):
        while True:
            args = my_input(
                'Please enter a language (The value of {target_lang} in prompt, e.g., Chinese, 中文) you want to translate into: ')
            args = line_to_args(args.strip())
            if len(args) >= 1:
                if len(args) == 1:
                    if args[0].lower() == 'q':
                        return False
                    else:
                        self._target = args[0]
                        return True

    def determine_translation_model(self):
        while True:
            args = my_input(
                'Please enter a model name (e.g., qwen:7b-instruct) you want to use: ')
            args = line_to_args(args.strip())
            if len(args) >= 1:
                if len(args) == 1:
                    if args[0].lower() == 'q':
                        return False
                    else:
                        self._model = args[0]
                        return True

    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)
        oconfig = config['translator']['open_ai']
        if self.args.auto:
            target_lang = oconfig['target_lang']
            model = oconfig['chat']['completions']['model']
            print(f'target_lang: {target_lang}')
            print(f'model: {model}')
        else:
            done = self.determine_translation_target()
            if not done:
                return False
            done = self.determine_translation_model()
            if not done:
                return False
            target_lang = self._target
            model = self._model
        _separator = oconfig['batch_separator']
        _max_len = oconfig['batch_max_textlen']
        _batch_size = oconfig['batch_size']
        self._open_ai = BatchTranslator(OpenAITranslator(model=model, target_lang=target_lang),
                                        _separator, _max_len, _batch_size)
        return True

    def translate(self, text: str):
        stripped_text = strip_or_none(text)
        if stripped_text is not None:
            return self._open_ai.translate(stripped_text)
        return text

    def translate_batch(self, texts: List[str]) -> List[str]:
        return self._open_ai.translate_batch(texts)

    def close(self):
        self._open_ai.close()


register_cmd_translator('openai', OpenAILibTranslator)

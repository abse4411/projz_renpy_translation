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
import copy
import logging
import time

from openai import OpenAI

from config import default_config
from trans import Translator


class OpenAITranslator(Translator):

    def __init__(self, model: str = None, target_lang: str = None, verbose: bool = True, ):
        '''

        :param model: The model to use.
        :param target_lang: The {target_lang} in the prompt.
        :param verbose: Print translation info
        '''
        self._target_lang = target_lang
        self._verbose = verbose
        config = default_config['translator']['open_ai']

        init_args = config['init']
        self._compl_args = copy.deepcopy(config['chat']['completions'])
        # set default model
        if model is not None:
            self._compl_args['model'] = model
        # set target_lang model
        if self._target_lang is None:
            self._target_lang = config.get('target_lang', 'Chinese')
        self._megs = copy.deepcopy(self._compl_args['messages'])
        self.token_count = 0
        self._client = OpenAI(**init_args)

    def translate(self, text: str) -> str:
        st_time = time.time()
        for m1, m2 in zip(self._compl_args['messages'], self._megs):
            m1['content'] = m2['content'].format(target_lang=self._target_lang, text=text)
        chat_completion = self._client.chat.completions.create(**self._compl_args)
        new_text = chat_completion.choices[0].message.content.rstrip()
        use_token = chat_completion.usage.total_tokens
        self.token_count += use_token
        if self._verbose:
            print(
                f'[Elapsed: {time.time() - st_time:.1f}s, TOKENS: USE {use_token}, ACC. {self.token_count}]: {text}->{new_text}')
        return new_text

    def close(self):
        try:
            print('Closing the OpenAI client...')
            self._client.close()
        except Exception as e:
            logging.exception(e)

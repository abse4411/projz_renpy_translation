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

from openai import OpenAI

from config import default_config
from trans import Translator


class OpenAITranslator(Translator):

    def __init__(self, verbose: bool = True, **template_kwargs):
        self._verbose = verbose
        config = default_config['translator']['open_ai']
        self._template_args = template_kwargs
        # template var should be removed since it is dynamic
        self._template_args.pop("text", None)

        init_args = config['init']
        self._compl_args = copy.deepcopy(config['chat']['completions'])
        # set default model
        model = template_kwargs.get('model', None)
        if model is not None:
            self._compl_args['model'] = model
        self._megs = copy.deepcopy(self._compl_args['messages'])

        self._client = OpenAI(**init_args)

    def translate(self, text: str) -> str:
        self._template_args['text'] = text
        for m1, m2 in zip(self._compl_args['messages'], self._megs):
            m1['content'] = m2['content'].format(**self._template_args)
        chat_completion = self._client.chat.completions.create(**self._compl_args)
        new_text = chat_completion.choices[0].message.content.rstrip()
        if self._verbose:
            print(f'{text}->{new_text}')
        return new_text

    def close(self):
        try:
            print('Closing the OpenAI client...')
            self._client.close()
        except Exception as e:
            logging.exception(e)


if __name__ == '__main__':
    t = OpenAITranslator(target_lang='Chinese')
    res = t.translate(
        "Welcome to the Nekomimi Institute, [playername]! My first name is [player.names[0]]. I like you [100.0 * points / max_points:.2] percent!")
    print(res)
    pass

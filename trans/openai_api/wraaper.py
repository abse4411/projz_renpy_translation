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


class SimpleMessageManager:
    def __init__(self, max_turns: int):
        assert max_turns > 0, f'max_turns({max_turns}) should be not less 0!'
        self._max_turns = max_turns
        self._sys_msg = []
        self._msgs = []

    def set_system_msg(self, msg):
        self._sys_msg = [msg]

    def put(self, user_msg, assistant_msg):
        self._msgs.append(user_msg)
        self._msgs.append(assistant_msg)
        if len(self._msgs) // 2 > self._max_turns:
            self._msgs = self._msgs[2:]

    def __len__(self):
        return len(self._sys_msg) + len(self._msgs)

    def to_list(self):
        return self._sys_msg + self._msgs


class OpenAITranslator(Translator):

    def __init__(self, model: str = None, target_lang: str = None, max_turns: int = None, verbose: bool = True):
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
        self._msgs = copy.deepcopy(self._compl_args['messages'])
        # find use message
        use_role = config.get('user_role', 'user')
        self._user_msg = None
        for m in self._msgs:
            if m['role'] == use_role:
                self._user_msg = copy.deepcopy(m)
        if self._user_msg is None:
            raise ValueError(f'Message with role={use_role} not found!')
        # find system message
        sys_msg = None
        for m in self._msgs:
            if m['role'] == 'system':
                sys_msg = copy.deepcopy(m)
                sys_msg['content'] = sys_msg['content'].format(target_lang=self._target_lang)
        # Manage messages
        if max_turns is None:
            max_turns = config.get('max_turns', 8)
        print(f'Max turn for chat is set to: {max_turns}')
        self._msg_manager = SimpleMessageManager(max_turns)
        if sys_msg is not None:
            self._msg_manager.set_system_msg(sys_msg)
        self.token_count = 0
        self._client = OpenAI(**init_args)

    def translate(self, text: str) -> str:
        st_time = time.time()
        user_msg = self._user_msg.copy()
        user_msg['content'] = self._user_msg['content'].format(target_lang=self._target_lang, text=text)
        self._compl_args['messages'] = self._msg_manager.to_list() + [user_msg]
        # print(f'Chat History: {len(self._msg_manager)}')
        # for m in self._msg_manager.to_list():
        #     print(f'\t{m}')
        chat_completion = self._client.chat.completions.create(**self._compl_args)
        assistant_msg = chat_completion.choices[0].message
        assistant_msg = {'role':assistant_msg.role, 'content': assistant_msg.content}

        # Put them to the message history
        self._msg_manager.put(user_msg, assistant_msg)

        new_text = assistant_msg['content'].rstrip()
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

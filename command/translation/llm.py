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

import tqdm

from command import BaseLangIndexCmd
from config import default_config
from store.database.base import flush
from store.group import group_translations_by, ALL
from trans.openai_api import OpenAITranslator
from util import strip_or_none
from util.renpy import strip_tags, is_translatable


class _InnerTranslator(OpenAITranslator):
    def __init__(self, model: str = None, target_lang: str = None, max_turns: int = None, verbose: bool = True):
        super().__init__(model, target_lang, max_turns, verbose)
        config = default_config['translator']['open_ai']
        self.assistant_role = config.get('assistant_role', 'assistant')

    def append_text(self, raw_text, new_text):
        user_msg = self._user_msg.copy()
        user_msg['content'] = self._user_msg['content'].format(target_lang=self._target_lang, text=raw_text)
        assistant_msg = {'role': self.assistant_role, 'content': new_text}
        # Put them to the message history
        self._msg_manager.put(user_msg, assistant_msg)

    def clear_chat(self):
        self._msg_manager.clear()


class LLMAugmentTranslateCmd(BaseLangIndexCmd):
    def __init__(self):
        super().__init__('llm_translate', 'Translate untranslated lines of the given language\n using '
                                          'the LLM Augment Translating.')
        self._cache_size = 100
        self._parser.add_argument('-m', '--model', help='The LLM model to use.')
        self._parser.add_argument('-t', '--target_lang', help='The {target_lang} in the prompt.')
        self._parser.add_argument("-a", "--auto", action='store_true',
                                  help="Load translation settings form config.")
        self._parser.add_argument("-ab", "--accept_blank", action='store_true',
                                  help="Accept blank translated lines from the translator when updating translations.")
        self._parser.add_argument('--limit', type=int, default=-1,
                                  help='The max number of lines to be translated. Negative values mean no limit.')

    def invoke(self):
        if self.args.auto:
            oconfig = default_config['translator']['open_ai']
            target_lang = oconfig['target_lang']
            model = oconfig['chat']['completions']['model']
            print(f'target_lang: {target_lang}')
            print(f'model: {model}')
        else:
            model = self.args.model
            target_lang = self.args.target_lang
            assert model and target_lang, (f'Both of model ({model}) and target_lang ({target_lang}) should provider '
                                           f'if arg "--auto" is not presented')
        cache_size = self.config['translator']['write_cache_size']
        if cache_size < 100:
            logging.warning(f'Low write_cache_size({cache_size}) means more frequent disk I/O operations,'
                            f' it may cause a high system load.')
        cache_size = max(cache_size, 100)

        n_untrans = 0
        index = self.get_translation_index()
        group_map = group_translations_by('filename', 'linenumber', ALL,
                                          index, self.args.lang, reverse=False,
                                          say_only=self.config.say_only)
        for g in group_map.values():
            for d in g:
                if d['new_text'] is None and is_translatable(d['old_text']):
                    n_untrans += 1
        if n_untrans == 0:
            print('No untranslated lines to translate.')
            return
        if self.args.limit >= 0:
            print(f'The max number of lines is set to {self.args.limit}.')
            n_untrans = min(self.args.limit, n_untrans)

        cnt = 0
        translator = _InnerTranslator(model, target_lang)
        tlist = []
        accept_blank = self.args.accept_blank
        try:
            with tqdm.tqdm(total=n_untrans, desc='Translating') as t:
                for g in group_map.values():
                    translator.clear_chat()
                    for d in g:
                        if d['new_text'] is None and is_translatable(d['old_text']):
                            raw_text = strip_or_none(strip_tags(d['old_text']))
                            if raw_text is None:
                                continue
                            else:
                                t.update(1)
                                cnt += 1
                                new_text = translator.translate(raw_text)
                                if new_text == raw_text:
                                    print(f'Discard untranslated line: {raw_text}')
                                else:
                                    if new_text.strip() == '' and not accept_blank:
                                        print(f'Discard blank line: {raw_text}')
                                    else:
                                        tlist.append((d['tid'], new_text))
                                if cnt > n_untrans:
                                    break
                                if cnt % cache_size == 0 and tlist:
                                    index.update_translations(self.args.lang, tlist, untranslated_only=True,
                                                              discord_blank=accept_blank, say_only=self.config.say_only)
                                    tlist = []
                                    print('Flushing...')
                                    flush()
                        else:
                            raw_text = strip_or_none(strip_tags(d['old_text']))
                            new_text = strip_or_none(strip_tags(d['new_text']))
                            if raw_text and new_text:
                                translator.append_text(raw_text, new_text)
                    if cnt > n_untrans:
                        break

        finally:
            translator.close()
        if tlist:
            index.update_translations(self.args.lang, tlist,
                                      untranslated_only=True, discord_blank=accept_blank,
                                      say_only=self.config.say_only)

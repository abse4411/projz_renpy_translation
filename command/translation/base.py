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

from command import BaseLangIndexCmd
from config import default_config
from store import TranslationIndex
from util import line_to_args

_TRANSLATOR = dict()


def register_cmd_translator(name: str, translator):
    assert name not in _TRANSLATOR, f'The {name} translator has already registered!'
    _TRANSLATOR[name] = translator


def unregister_cmd_translator(name):
    if name in _TRANSLATOR:
        return _TRANSLATOR.pop(name)


class TranslateCmd(BaseLangIndexCmd):
    def __init__(self):
        self.reinit()

    def reinit(self):
        super().__init__('translate', 'Translate untranslated lines of the given language\n using '
                                      'the specified translator.')
        self._parser.add_argument("-t", "--translator", type=str, choices=list(_TRANSLATOR.keys()), required=True,
                                  help="The translator to use.")
        self._parser.add_argument("-ab", "--accept_blank", action='store_true',
                                  help="Accept blank translated lines from the translator when updating translations.")
        self._parser.add_argument('--limit', type=int, default=-1,
                                  help='The max number of lines to be translated. Negative values mean no limit.')
        self._translator = None

    def get_untranslated_lines(self):
        index = self.get_translation_index()
        tids_and_texts = index.get_untranslated_lines(self.args.lang, say_only=self.config.say_only)
        if self.args.limit >= 0:
            tids_and_texts = tids_and_texts[:self.args.limit]
            print(f'The max number of lines is set to {self.args.limit}.')
        if not tids_and_texts:
            print('No untranslated lines to translate.')
        else:
            res = []
            if tids_and_texts:
                if tids_and_texts:
                    for tid, raw_text in tids_and_texts:
                        if raw_text.strip() == '':
                            continue
                        res.append([tid, raw_text])
            tids_and_texts = res
        return tids_and_texts, index

    def parse_args(self, text: str):
        # we create new _parser as we don't know what args dose _translator.register_args
        self.reinit()
        args_list = line_to_args(text)
        # we let _translator register its args if user specify --translator and --help args
        # this enables to show help of _translator
        if ('-h' in args_list or '--help' in args_list) and ('-t' in args_list or '--translator' in args_list):
            try:
                tmp_args = args_list.copy()
                if '-h' in args_list:
                    tmp_args.remove('-h')
                if '--help' in args_list:
                    tmp_args.remove('--help')
                if tmp_args and tmp_args[0].startswith('-'):
                    # we pass a valid but useless index to suppress possible parsing error
                    tmp_args = ['foo'] + tmp_args
                tmp_args.append('-l foo')
                self.args, _ = self._parser.parse_known_args(tmp_args)
            except SystemExit:
                pass
        else:
            self.args, _ = self._parser.parse_known_args(args_list)

        # used for BaseIndexCmd
        self._translator = _TRANSLATOR[self.args.translator]()
        self._translator.register_args(self._parser)
        self.args = self._parser.parse_args(args_list)
        self._index, self._nick_name = self.parse_index_or_name(self.args.index_or_name)

    def invoke(self):
        done = self._translator.do_init(self.args, default_config)
        if not done:
            print('Translation task is canceled.')
            return
        tids_and_texts, index = self.get_untranslated_lines()

        if tids_and_texts:
            tid_map = {tid: text for tid, text in tids_and_texts}
            accept_blank = self.args.accept_blank

            def _update(tlist):
                use_cnt = 0
                new_tlist = []
                if tlist:
                    for tid, new_text in tlist:
                        if TranslationIndex.is_valid_tid(tid):
                            raw_text = tid_map.get(tid, None)
                            if raw_text is not None:
                                if new_text == raw_text:
                                    print(f'Discard untranslated line: {raw_text}')
                                else:
                                    if new_text.strip() == '' and not accept_blank:
                                        print(f'Discard blank line: {raw_text}')
                                    else:
                                        use_cnt += 1
                                        new_tlist.append((tid, new_text))
                                        continue
                    print(f'Find {use_cnt} translated lines, and discord {len(tlist) - use_cnt} lines')
                    index.update_translations(self.args.lang, new_tlist,
                                              untranslated_only=True, discord_blank=accept_blank,
                                              say_only=self.config.say_only)
            self._translator.invoke(tids_and_texts, _update)

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
from collections import defaultdict

from prettytable import PrettyTable, prettytable

from command import BaseConfirmationCmd, BaseIndexConfirmationCmd, BaseLangIndexConfirmationCmd, BaseLangIndexCmd
from command.base import BaseCmd, BaseIndexCmd
from store import TranslationIndex
from store.database.base import db_context
from util import yes, quick_prettytable


class ListTranslationIndexCmd(BaseCmd):
    def __init__(self):
        super().__init__('ls', 'List existing TranslationIndexes.')

    def invoke(self):
        res = TranslationIndex.list_indexes()
        table = PrettyTable(['Index', 'Nickname:tag', 'Translation Stats', 'Injection state', 'Game info'])
        table.hrules = prettytable.ALL

        def format_stats(stats: dict):
            stable = PrettyTable(['Language', 'Dialogue', 'String', 'Sum'])
            stable.vrules = prettytable.NONE
            stable.hrules = prettytable.NONE
            merged_dict = defaultdict(lambda: defaultdict(lambda: (0, 0)))
            if stats:
                for lang, v in stats['dialogue'].items():
                    merged_dict[lang][0] = v
                for lang, v in stats['string'].items():
                    merged_dict[lang][1] = v
                for lang, vs in merged_dict.items():
                    d = vs[0]
                    s = vs[1]
                    stable.add_row([lang, f'{d[0]}/{d[1]}', f'{s[0]}/{s[1]}', sum(d[:2] + s[:2])])
                    # str_res += f'\n{lang} {d[0]}/{d[1]} {s[0]}/{s[1]} {)}'
            return stable if len(merged_dict) > 0 else ''

        for i in res:
            index = i[1]
            injection_table = quick_prettytable([[k, v] for k, v in index.injection_state.items()])
            injection_table.vrules = prettytable.NONE
            injection_table.hrules = prettytable.NONE
            game_info = (f'{index.project_name}-V{index.project_version}, {index.project_renpy_version}\n'
                         f'{index.project_path}')
            table.add_row([i[0], f'{index.nickname}:{index.tag}', format_stats(index.translation_state),
                           injection_table, game_info])
        print('Note that: Translation Stats list translated/untranslated lines '
              'of dialogue and string for each language.')
        print(table)


class ClearAllTranslationIndexCmd(BaseConfirmationCmd):
    def __init__(self):
        super().__init__('clear', 'Clear all existing TranslationIndex.')

    @db_context
    def invoke(self):
        if self.args.yes or yes(f'Are your sure to clear?'):
            res = TranslationIndex.list_indexes()
            for i in res:
                TranslationIndex.remove_index(i[0])


class DeleteTranslationIndexCmd(BaseIndexConfirmationCmd):
    def __init__(self):
        super().__init__('del', 'Delete the TranslationIndex.')

    def invoke(self):
        if self.args.yes or yes(f'Are your sure to delete?'):
            TranslationIndex.remove_index(self._index, self._nick_name)


class DiscardTranslationCmd(BaseLangIndexConfirmationCmd):
    def __init__(self):
        super().__init__('discard', 'Discard translations with the given language.')

    @db_context
    def invoke(self):
        if self.args.yes or yes(f'Are your sure to drop?'):
            index = self.get_translation_index()
            index.drop_translations(self.args.lang)


class RenameLanguageCmd(BaseLangIndexCmd):
    def __init__(self):
        super().__init__('rename', 'Rename a name of language translations.')
        self._parser.add_argument("-t", "--target", required=True, type=str, metavar='new_lang',
                                  help="The new name.")

    @db_context
    def invoke(self):
        index = self.get_translation_index()
        index.rename_lang(self.args.lang, self.args.target)


class ClearUntranslationIndexCmd(BaseLangIndexConfirmationCmd):
    def __init__(self):
        super().__init__('mark', 'Mark all untranslated lines as translated ones.')

    def invoke(self):
        if self.args.yes or yes(f'Are your sure to make all untranslated lines as translated ones?'):
            index = self.get_translation_index()
            index.clear_untranslated_lines(self.args.lang, say_only=self.config.say_only)


class UpdateTranslationStatsCmd(BaseIndexCmd):
    def __init__(self):
        super().__init__('upstats', 'Update translation stats of the specified TranslationIndex.')
        self._parser.add_argument("-l", "--lang", default=None, type=str, metavar='language',
                                  help="The language to update. Update all languages when not passing this arg.")

    @db_context
    def invoke(self):
        index = self.get_translation_index()
        index.update_translation_stats(self.args.lang, say_only=self.config.say_only)


class MergeTranslationCmd(BaseLangIndexConfirmationCmd):
    def __init__(self):
        super().__init__('merge', 'Merge translations of the given language '
                                  'from another TranslationIndex.')
        self._parser.add_argument("-s", "--source", required=True, type=str, metavar='another_index',
                                  help="The index or nickname of another TranslationIndex.")

    @db_context
    def invoke(self):
        target = self.get_translation_index()
        source = TranslationIndex.from_docid_or_nickname(*self.parse_index_or_name(self.args.source))
        assert source is not None, \
            'Could\'n load this TranslationIndex. Please check whether the entered index or nickname is correct'
        if self.args.yes or yes(
                f'Are you sure to merge translations of language {self.args.lang} from {source.nickname}:{source.tag} '
                f'into {target.nickname}:{target.tag}?'):
            target.merge_translations_from(source, self.args.lang, say_only=self.config.say_only)

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
import os.path

import prettytable
from prettytable import PrettyTable

from command import BaseCmd
from command.base import BaseIndexCmd
from injection import Project
from injection.cmd import lang_project
from injection.default import RENPY_GAME_DIR, RENPY_TL_DIR
from store import TranslationIndex
from util import walk_and_select


class NewTranslationIndexCmd(BaseCmd):
    def __init__(self):
        super().__init__('new', 'Create a TranslationIndex from the given game path.')
        self._parser.add_argument('game_path', type=str, help='The RenPy game path which includes *.exe')
        self._parser.add_argument("-n", "--name", required=False, type=str, metavar='nickname',
                                  help="A nickname for this TranslationIndex. "
                                       "You can use it to specify a TranslationIndex. We will generate a random one "
                                       "if this args is not presented.")
        self._parser.add_argument("-t", "--tag", required=False, type=str, metavar='tag',
                                  help="A tag for for this TranslationIndex.")

    def invoke(self):
        index = TranslationIndex.from_dir(self.args.game_path, self.args.name, self.args.tag)
        index.save()


class ImportTranslationCmd(BaseIndexCmd):
    def __init__(self):
        super().__init__('import', 'Import translations of the given language into this '
                                   'TranslationIndex. (Base injection required)')
        self._parser.add_argument("-l", "--lang", required=True, type=str, metavar='language',
                                  help="The language to import.")
        self._parser.add_argument("-to", "--translated_only", action='store_true',
                                  help="Only import translated texts. The translated texts means translations "
                                       "listed in ryp files in you_game/game/tl/{lang} dir.")

    def invoke(self):
        self.get_translation_index().import_translations(self.args.lang, self.args.translated_only, say_only=True)


class GenerateTranslationCmd(BaseIndexCmd):
    def __init__(self):
        super().__init__('generate', 'Generate translations of the given language from this '
                                     'TranslationIndex. (Base injection required)')
        self._parser.add_argument("-l", "--lang", required=True, type=str, metavar='language',
                                  help="The language to generate.")
        self._parser.add_argument("-a", "--all", action='store_true',
                                  help="Generate all translated and translated texts. "
                                       "If this arg is not specified, only translated text are used to generate.")
        self._parser.add_argument("-f", "--force", action='store_true',
                                  help="Clear all rpy/rpyc files in game/tl/{lang} before generating. "
                                       "You can use this arg to overwrite existing translations in rpy/rpyc files.")

    def invoke(self):
        index = self.get_translation_index()
        if self.args.force:
            rpy_files = walk_and_select(os.path.join(index.project_path, RENPY_GAME_DIR, RENPY_TL_DIR, self.args.lang),
                                        select_fn=lambda x: x.endswith('.rpy') or x.endswith('.rpyc'))
            for r in rpy_files:
                print(f'Deleting {r}')
                os.remove(r)
        index.export_translations(self.args.lang, not self.args.all, say_only=True)


class CountTranslationCmd(BaseIndexCmd):
    def __init__(self):
        super().__init__('count', 'Print a count of missing translations of the given language.'
                                  ' (Base injection required)')
        self._parser.add_argument("-l", "--lang", required=True, type=str, metavar='language',
                                  help="The language to count.")
        self._parser.add_argument("-p", "--print", action='store_true',
                                  help="Print each missed translation.")

    def invoke(self):
        self.get_translation_index().count_translations(self.args.lang, show_detail=self.args.print, say_only=True)


class LaunchProjectCmd(BaseIndexCmd):
    def __init__(self):
        super().__init__('launch', 'Launch the RenPy game associated with the TranslationIndex.')

    def invoke(self):
        lang_project(self.get_translation_index().project, wait=False)


INJECTION_TYPES = {
    Project.BASE_INJECTION: "The basic injection which allows you to import, generate, count translations from a\n"
                            "RenPy game. This injection will be done automatically when executing the \"new\" command.",
    Project.I18N_INJECTION: "The i18n injection creates a menu for a RenPy game, where you can change the language\n"
                            "or font dynamically. Also, you can show this menu by using a shortcut key or click the\n"
                            "button named \"i18n settings\" in game's preference menu. The shortcut key can be \n"
                            "configured in config.yaml. The languages listed in the menu is determined by the dirs\n"
                            "in your_game/game/tl.",
}


def _print_injection_types():
    table = PrettyTable(['Injection type', 'Description'])
    table.hrules = prettytable.ALL
    for k, v in INJECTION_TYPES.items():
        table.add_row([k, v])
    print(table)


class InjectionCmd(BaseIndexCmd):
    def __init__(self):
        super().__init__('inject', 'Launch the RenPy game associated with the TranslationIndex.')
        self._parser.add_argument("-t", "--type", default=Project.BASE_INJECTION, type=str, metavar='injection_type',
                                  choices=list(INJECTION_TYPES.keys()),
                                  help="The injection type to inject into the game.")
        self._parser.add_argument("-l", "--list", action='store_true',
                                  help="List available injection types.")
        self._parser.add_argument("-u", "--undo", action='store_true',
                                  help="Undo the specified injection.")

    def parse_args(self, text: str):
        args = text.split()
        # we don't change the text if '--help' arg found in it
        if not ('-h' in args or '--help' in args) and ('-l' in args or '--list' in args):
            # if '--list' found, we pass a valid but useless text to suppress possible parsing error
            text = 'foo --list'
        super().parse_args(text)

    def invoke(self):
        if self.args.list:
            _print_injection_types()
            return
        injection_type = self.args.type
        index = self.get_translation_index()
        if injection_type == Project.BASE_INJECTION:
            injection = index.project.get_base_injection()
        elif injection_type == Project.I18N_INJECTION:
            injection = index.project.get_i18n_injection()
        else:
            raise NotImplementedError(injection_type)
        if self.args.undo:
            res = injection.undo()
            print(f'Undo result : {res}')
        else:
            res = injection()
            print(f'Injection result : {res}')
        # save injection state
        index.save()
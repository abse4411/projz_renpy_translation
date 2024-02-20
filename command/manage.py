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
from io import StringIO
from typing import Any

from prettytable import PrettyTable, prettytable

from command import *
from util import assert_not_blank

_SHORT_NAME_MAP = {}
_REGISTERED_CMDS = {}


def exists_cmd(name: str):
    return name in _REGISTERED_CMDS


def exists_short_cmd(name: str):
    return name in _SHORT_NAME_MAP


def register(cmd: BaseCmd, short_name: str = None):
    name = assert_not_blank(cmd.name, 'name')
    if short_name:
        short_name = assert_not_blank(short_name, 'short_name')
        assert not exists_cmd(short_name), f'Existing command {short_name} have been already registered'
    assert not exists_cmd(name), f'Existing command {name} have been already registered'
    _REGISTERED_CMDS[name] = cmd
    _REGISTERED_CMDS[short_name] = cmd
    _SHORT_NAME_MAP[name] = short_name


def unregister(name: str):
    name = assert_not_blank(name, 'name')
    if exists_cmd(name):
        _REGISTERED_CMDS.pop(name)
        if exists_short_cmd(name):
            _REGISTERED_CMDS.pop(_SHORT_NAME_MAP[name])


EXIT = False


class QuitCmd(BaseCmd):
    def __init__(self):
        super().__init__('quit', 'Quit the program.')

    def invoke(self):
        global EXIT
        print('Have a nice day! Bye bye! :-)')
        # Instead of exit(0), we exit in execute_cmd()
        EXIT = True


def execute_cmd(name: str, cmd_line: str):
    name = assert_not_blank(name, 'name')
    try:
        cmd = _REGISTERED_CMDS[name]
        cmd.parse_args(cmd_line)
    except SystemExit:
        # we don't want to exit when parsing error or showing help
        return
    cmd.invoke()
    # this can be set by QuitCmd
    if EXIT:
        exit(0)


def all_cmds():
    return list(_SHORT_NAME_MAP.keys())


class HelpCmd(BaseCmd):
    def __init__(self):
        super().__init__('help', 'Print name and description of each command.')
        self._parser.add_argument('-u', '--usage', action='store_true',
                                  help='Show usage for each command')

    def invoke(self):
        table = PrettyTable(
            ['Command name', 'Description'])
        table.hrules = prettytable.ALL
        for name in all_cmds():
            cmd = _REGISTERED_CMDS[name]
            description = cmd.description
            if self.args.usage:
                usage = StringIO()
                cmd.__getattribute__('_parser').print_usage(file=usage)
                description += '\n' + usage.getvalue().strip()
            short_name = _SHORT_NAME_MAP.get(name, None)
            if short_name:
                append = f' | {short_name}'
            else:
                append = ''
            table.add_row([name + append, description])
        print(table)


# Interacting with RenPy
register(NewTranslationIndexCmd(), short_name='n')
register(NewFileTranslationIndexCmd(), short_name='nf')
register(ImportTranslationCmd(), short_name='i')
register(GenerateTranslationCmd(), short_name='g')
register(CountTranslationCmd(), short_name='c')
register(OpenProjectCmd(), short_name='o')
register(LintProjectCmd())
register(LaunchProjectCmd())
register(InjectionCmd(), short_name='ij')

# Translator
register(TranslateCmd(), short_name='t')

# Operations for TranslationIndex
register(ListTranslationIndexCmd(), short_name='l')
register(DeleteTranslationIndexCmd())
register(ClearAllTranslationIndexCmd())
register(DiscardTranslationCmd())
register(RenameLanguageCmd())
register(CopyLanguageCmd())
register(ClearUntranslationIndexCmd())
register(ClearTranslationIndexCmd())
register(UpdateTranslationStatsCmd())
register(MergeTranslationCmd(), short_name='m')

# Read/Write translations from/to files
register(SaveHtmlCmd(), short_name='sh')
register(LoadHtmlCmd(), short_name='lh')
register(SaveExcelCmd(), short_name='se')
register(LoadExcelCmd(), short_name='le')
register(DumpExcelCmd(), short_name='de')
register(DumpErrorExcelCmd())
register(UpdateExcelCmd(), short_name='ue')
register(SaveJsonCmd(), short_name='sj')
register(LoadJsonCmd(), short_name='lj')

# For users
register(HelpCmd(), short_name='h')
register(QuitCmd(), short_name='q')

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
from typing import List, Tuple

from command.translation.base import register
from config.base import ProjzConfig
from translator.base import ConcurrentTranslatorTemplate
from translator.base.template import CachedTranslatorTemplate

_WEB_APIS = dict()


class BaseWebTranslator(CachedTranslatorTemplate):
    def __init__(self):
        super().__init__()

    def register_args(self, parser: ArgumentParser):
        '''
        Don't call this in subclass
        :param parser:
        :return:
        '''
        raise NotImplementedError()

    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)


def register_translator(name: str, translator):
    assert name not in _WEB_APIS, f'The {name} translator has already registered!'
    _WEB_APIS[name] = translator


def unregister_translator(name):
    if name in _WEB_APIS:
        return _WEB_APIS.pop(name)


class WebConcurrentTranslator(ConcurrentTranslatorTemplate):

    def __init__(self):
        super().__init__()

    def register_args(self, parser: ArgumentParser):
        super().register_args(parser)
        parser.add_argument('-n', '--name', choices=list(_WEB_APIS.keys()), default='google',
                            help='The name of web translator.')

    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)
        super().create_taskrunner(_WEB_APIS[args.name], count_on_batch=False, wait_for_init=True,
                                  wait_prompt='Now you can do any operation on these opened browsers, '
                                              'like setting your translation setting: English -> Chinese.')

    def invoke(self, tids_and_text: List[Tuple[str, str]], update_func):
        super().invoke(tids_and_text, update_func)


register('web', WebConcurrentTranslator)

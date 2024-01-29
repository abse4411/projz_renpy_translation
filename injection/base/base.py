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


class BaseInjector:

    def __call__(self, *args, **kwargs):
        '''
        Do injection
        :param args:
        :param kwargs:
        :return: True if injected successfully, otherwise False
        '''
        raise NotImplementedError()

    def undo(self, *args, **kwargs):
        '''
        Undo injection
        :param args:
        :param kwargs:
        :return: False if failed to undo injection, otherwise True
        '''
        raise NotImplementedError()


class UndoOnFailedCallInjector(BaseInjector):
    def __init__(self, injector):
        self.injector = injector

    def __call__(self, *args, **kwargs):
        done = True
        try:
            done = self.injector(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
            done = False
        if not done:
            try:
                self.injector.undo()
            except Exception as e:
                logging.exception(e)
        return done

    def undo(self, *args, **kwargs):
        try:
            return self.injector.undo(*args, **kwargs)
        except Exception as e:
            logging.exception(e)
            return False

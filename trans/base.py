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
from typing import List


class Translator:
    def translate(self, text: str) -> str:
        return text

    def translate_batch(self, texts: List[str]) -> List[str]:
        return [self.translate(t) for t in texts]

    def close(self):
        '''
        Release resources if necessary
        :return:
        '''
        pass
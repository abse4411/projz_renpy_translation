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
from typing import List, Any

from prettytable import PrettyTable


def my_input(prompt):
    print(prompt, flush=True)
    return input()


def yes(prompt):
    y = my_input(prompt + ' Enter Yes/Y (case-insensitive) to proceed:')
    y = y.strip().lower()
    if y == 'y' or y == 'yes':
        return True
    return False


def quick_prettytable(arr_2d: List[List[Any]], transposed: bool = False):
    r"""
    Build a PrettyTable object from a 2D array.

    :param arr_2d: 2D array
    :param transposed: if true, each row in arr_2d is mapped to a col in returned PrettyTable
    :return:
    """
    if len(arr_2d) == 0 or len(arr_2d[0]) == 0:
        return PrettyTable()

    if transposed:
        table = PrettyTable()
        n_row = len(arr_2d)
        n_col = len(arr_2d[0])
        for i in range(n_col):
            items = [arr_2d[j][i] for j in range(n_row)]
            table.add_column(items[0], items[1:])
    else:
        table = PrettyTable(arr_2d[0])
        for row in arr_2d[1:]:
            table.add_row(row)
    return table

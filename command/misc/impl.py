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
from command import BaseCmd
from config.base import CONFIG_FILE


class ReloadConfigCmd(BaseCmd):
    def __init__(self):
        super().__init__('reconfig', 'Reload config from disk. It takes effect for most config items.')
        self._parser.add_argument("-f", "--file", default=CONFIG_FILE, type=str, metavar='config_path',
                                  help=f"The path to config.yaml.")

    def invoke(self):
        print(f'Reload config file from {self.args.file}')
        self.config.reload(self.args.file)

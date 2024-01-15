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

from command import BaseCmd
from command.manage import exists_cmd, execute_cmd, all_cmds, register
from util import my_input
import translator

__VERSION__ = '0.4.0'


def print_banner():
    print(fr'''
________  ________  ________        ___  ________     
|\   __  \|\   __  \|\   __  \      |\  \|\_____  \    
\ \  \|\  \ \  \|\  \ \  \|\  \     \ \  \\|___/  /|   
 \ \   ____\ \   _  _\ \  \\\  \  __ \ \  \   /  / /   
  \ \  \___|\ \  \\  \\ \  \\\  \|\  \\_\  \ /  /_/__  
   \ \__\    \ \__\\ _\\ \_______\ \________\\________\
    \|__|     \|__|\|__|\|_______|\|________|\|_______|   V{__VERSION__}''')
    print("RenPy机翻工具 - A translator for RenPy games. This project is under the GPL-3.0 license.")
    print(f"By abse4411. Link: https://github.com/abse4411/projz_renpy_translation")


class PrintBannerCmd(BaseCmd):
    def __init__(self):
        super().__init__('foo', 'Print our banner just for fun.')

    def invoke(self):
        print_banner()


register(PrintBannerCmd())


def main():
    print_banner()
    execute_cmd('help', '')
    while True:
        args = my_input('What is your next step? (Enter a command (case insensitive) or Q/q to exit): ')
        args = args.strip()
        args = [c.strip() for c in args.split() if c.strip() != '']
        if len(args) >= 1:
            cmd_name = args[0].lower()
            if exists_cmd(cmd_name):
                try:
                    execute_cmd(cmd_name, ' '.join(args[1:]))
                except Exception as e:
                    print(f'error: {e}')
                    logging.exception(e)
            else:
                print(
                    f'Sorry, it seems to be an invalid command. Available commands are {all_cmds()}.')
    pass


# package cmd: pyinstaller -i imgs/proz_icon.ico -F main.py --copy-metadata tqdm --copy-metadata regex --copy-metadata requests --copy-metadata packaging --copy-metadata filelock --copy-metadata numpy --copy-metadata tokenizers --copy-metadata huggingface-hub --copy-metadata safetensors --copy-metadata accelerate --copy-metadata pyyaml --copy-metadata sentencepiece
if __name__ == '__main__':
    import log  # enable logging
    main()

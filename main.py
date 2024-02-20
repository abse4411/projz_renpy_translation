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
from util import my_input, line_to_args
import translator

__VERSION__ = '0.4.2'


def print_banner():
    print(fr'''----------Projz - RenyPy Translation Toolkit----------
________  ________  ________        ___  ________     
|\   __  \|\   __  \|\   __  \      |\  \|\_____  \    
\ \  \|\  \ \  \|\  \ \  \|\  \     \ \  \\|___/  /|   
 \ \   ____\ \   _  _\ \  \\\  \  __ \ \  \   /  / /   
  \ \  \___|\ \  \\  \\ \  \\\  \|\  \\_\  \ /  /_/__  
   \ \__\    \ \__\\ _\\ \_______\ \________\\________\
    \|__|     \|__|\|__|\|_______|\|________|\|_______|   V{__VERSION__}
RenPy机翻工具 - A translator for RenPy games. This project is under the GPL-3.0 license.
By abse4411.  Source code: https://github.com/abse4411/projz_renpy_translation, License: https://github.com/abse4411/projz_renpy_translation?tab=GPL-3.0-1-ov-file
# 🔗Acknowledgement
The codes or libs we use or refer to:
* Previous code of Web translation: [Maooookai(Mirage)](https://github.com/Maooookai/WebTranslator), [DrDRR](https://github.com/drdrr/RenPy-WebTranslator)
* AI translation: [dl-translate](https://github.com/xhluca/dl-translate), [MIT License](https://github.com/xhluca/dl-translate?tab=MIT-1-ov-file)
* [UlionTse/translators](https://github.com/UlionTse/translators), [GPL-3.0 License](https://github.com/UlionTse/translators?tab=GPL-3.0-1-ov-file)
* Pre-translated RPY file: [RenPy](https://github.com/renpy/renpy/tree/master/launcher/game/tl), [MIT License for these rpy files](https://www.renpy.org/doc/html/license.html)
* [resources/codes/projz_injection.py](resources/codes/projz_injection.py): [RenPy](https://github.com/renpy/renpy/blob/master/renpy/translation/generation.py), [MIT License for the code file](https://www.renpy.org/doc/html/license.html)
* Other python libs：[requirements.txt](./requirements.txt)
''')


class AboutCmd(BaseCmd):
    def __init__(self):
        super().__init__('about', 'About me.')

    def invoke(self):
        print_banner()


register(AboutCmd())


def main():
    # print_banner()
    execute_cmd('help', '')
    while True:
        cmd_line = my_input('What is your next step? (Enter a command (case insensitive) or Q/q to exit): ')
        args = cmd_line.strip()
        args = line_to_args(args)
        if len(args) >= 1:
            cmd_name = args[0].lower()
            if exists_cmd(cmd_name):
                try:
                    cmd_line = cmd_line.replace(args[0], '', 1)
                    execute_cmd(cmd_name, cmd_line)
                except Exception as e:
                    logging.exception(e)
            else:
                print(
                    f'Sorry, it seems to be an invalid command. Available commands are {all_cmds()}.')
    pass


# package cmd: pyinstaller -i imgs/proz_icon.ico -F main.py --copy-metadata tqdm --copy-metadata regex \
# --copy-metadata requests --copy-metadata packaging --copy-metadata filelock --copy-metadata numpy \
# --copy-metadata tokenizers --copy-metadata huggingface-hub --copy-metadata safetensors --copy-metadata accelerate \
# --copy-metadata pyyaml --copy-metadata sentencepiece
if __name__ == '__main__':
    import log  # enable logging
    main()

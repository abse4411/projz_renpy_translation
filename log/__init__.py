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
import os.path
import sys
import time

from config import default_config
from util import mkdir


def create_log(fmt='[%(asctime)s][%(filename)s:%(lineno)d, %(thread)d][%(levelname)s]: %(message)s',
               datefmt='%Y-%m-%d %H:%M:%S'):
    if default_config.enable_log:
        logger = logging.getLogger()
        # Log level
        logger.setLevel(default_config.log_level)
        # Formatting
        formatter = logging.Formatter(fmt, datefmt)
        # create log file
        mkdir(default_config.log_path)
        log_file = os.path.join(default_config.log_path, time.strftime('PROZ_%Y-%m-%d-%H-%M-%S.log'))
        print(f'Log file is saved to {log_file}')
        fhandler = logging.FileHandler(log_file, encoding='utf-8', delay=True)
        fhandler.setLevel(default_config.log_level)
        fhandler.setFormatter(formatter)
        logger.addHandler(fhandler)
        # log to console
        if default_config.console_log:
            console_handler = logging.StreamHandler(stream=sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)


create_log()

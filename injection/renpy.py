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

import glob
import json
import logging
import os.path
import subprocess
import uuid
from typing import List, Dict, Tuple

from config import default_config
from injection.base import BaseInjector
from injection.base.base import UndoOnFailedCallInjector, call_chain, undo_chain
from injection.default import RENPY_DIRS, PYTHON_LINUX64_EXE, PYTHON_WIN64_EXE, PYTHON_WIN32_EXE, PYTHON_LINUX32_EXE, \
    RENPY_LIB_DIR, ProjzI18nInjection, ProjzCmdInjection, try_running, RENPY_GAME_DIR, RENPY_TL_DIR
from util import exists_dir, file_name_ext, exists_file, default_read, default_write, file_dir, strip_or_none
from util import is_windows, is_x64


def check_renpy_dir(abs_path):
    assert exists_dir(abs_path), f'{abs_path} is not a dir!'
    for d in RENPY_DIRS:
        absd = os.path.join(abs_path, d)
        assert exists_dir(absd), f'The dir({d}) is required in {abs_path}!'


def check_project_name(abs_path):
    py_files = [file_name_ext(f)[0] for f in glob.glob(os.path.join(abs_path, '*.py'))]
    sh_files = [file_name_ext(f)[0] for f in glob.glob(os.path.join(abs_path, '*.sh'))]
    exe_files = [file_name_ext(f)[0] for f in glob.glob(os.path.join(abs_path, '*.exe'))]

    project_name = None
    if is_windows():
        same_name_files = exe_files
    else:
        same_name_files = sh_files

    for py_name in py_files:
        if py_name in same_name_files:
            project_name = py_name
            break
    assert project_name is not None, f'Coundn\'t find a entrypoint file in {abs_path}'
    return project_name


def check_python_exe(abs_path):
    executable_path = None
    lib_path = os.path.join(abs_path, RENPY_LIB_DIR)
    if is_windows():
        pyexe_files = PYTHON_WIN64_EXE + PYTHON_WIN32_EXE
    else:
        pyexe_files = PYTHON_LINUX64_EXE + PYTHON_LINUX32_EXE
    pyexe_files = [os.path.join(lib_path, exe) for exe in pyexe_files]
    for pyexe in pyexe_files:
        if exists_file(pyexe):
            executable_path = pyexe
            break
    assert executable_path is not None, f'Coundn\'t find a executable file file in {lib_path}'
    return executable_path


def check_ok_json(file, uuid_str, verbose=False):
    if exists_file(file):
        with default_read(file) as f:
            data = json.load(f)
        if verbose:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        if 'ok' in data and 'uuid' in data:
            return data['ok'] is True and data['uuid'] == uuid_str, data
    return False, None


class ProjectInjector(BaseInjector):
    def __init__(self, p, name, injector):
        self.p = p
        self.name = name
        self.injector = injector

    def __call__(self, *args, **kwargs):
        res = self.injector(*args, **kwargs)
        self.p.set_injection_state(self.name, res)
        return res

    def undo(self, *args, **kwargs):
        res = self.injector.undo(*args, **kwargs)
        self.p.set_injection_state(self.name, not res)
        return res


class Project:
    BASE_INJECTION = "Base"
    I18N_INJECTION = "I18n"

    def __init__(self, project_path: str, executable_path: str, project_name: str,
                 game_info: Dict[str, str] = None, injection_state: Dict[str, bool] = None):
        self._project_path = project_path
        self._executable_path = executable_path
        self._project_name = project_name
        self._game_info = game_info if game_info is not None else dict()
        self._injection_state = injection_state if injection_state is not None else dict()

    @property
    def project_path(self):
        return self._project_path

    @property
    def executable_path(self):
        return self._executable_path

    @property
    def project_name(self):
        return self._project_name

    @property
    def game_info(self):
        return self._game_info

    @property
    def injection_state(self):
        return self._injection_state

    @property
    def game_dir(self):
        return os.path.join(self.project_path, RENPY_GAME_DIR)

    @property
    def tl_dir(self):
        return os.path.join(self.project_path, RENPY_GAME_DIR, RENPY_TL_DIR)

    def set_game_info(self, data: Dict[str, str]):
        self._game_info = data

    def register_injection(self, name, injector):
        return ProjectInjector(self, name, injector)

    def get_base_injection(self):
        return self.register_injection(self.BASE_INJECTION, UndoOnFailedCallInjector(
            ProjzCmdInjection(self.project_path)))

    def get_i18n_injection(self, languages: List[str] = None):
        return self.register_injection(self.I18N_INJECTION, UndoOnFailedCallInjector(
            ProjzI18nInjection(self.project_path, languages=languages)))

    def set_injection_state(self, name, value):
        self._injection_state[name] = value

    def get_injection_state(self, name, default_value=None):
        return self._injection_state.get(name, default_value)

    def get_injection_names(self):
        return [self._injection_state.keys()]

    def launch(self, cmd, args: List[str], verbose=False, wait=False):
        cmd_args = None
        if 'i686' in self.executable_path:
            new_ext = '.exe' if is_windows() else ''
            new_exe = os.path.join(file_dir(self.executable_path), self.project_name + new_ext)
            if exists_file(new_exe):
                cmd_args = [new_exe, self.project_path, cmd] + args
        if cmd_args is None:
            # Put the command and args together.
            cmd_args = [self.executable_path, os.path.join(self.project_path, f'{self.project_name}.py'),
                        self.project_path, cmd] + args
        if verbose:
            logging.info(f'Launching: {" ".join(cmd_args)}')
        cmd_args = list(filter(lambda x: strip_or_none(x), cmd_args))
        # raise RuntimeError()
        # print(cmd_line)
        # we don't send any input to subprocess
        p = subprocess.Popen(cmd_args, shell=True, stdin=subprocess.PIPE)
        if wait:
            return_code = p.wait()
            if verbose:
                logging.info(f'Subprocess returns code: {return_code}')
            return return_code
        return None

    def launch_task(self, payload, args: List[str], verbose=False, clear_cache=True):
        assert self.get_injection_state(self.BASE_INJECTION), f'Please do the {self.BASE_INJECTION} Injection first'
        str_id = uuid.uuid1().hex
        json_file = os.path.join(default_config.tmp_path, f'{str_id}.json')

        try:
            with default_write(json_file) as f:
                json.dump({'uuid': str_id, 'items': payload}, f, ensure_ascii=False, indent=2)
            print('Launching a new task...')
            code = self.launch('projz_inject_command', args=[json_file, '--uuid', str_id] + args, verbose=verbose,
                               wait=True)
            if code == 0:
                ok, data = check_ok_json(json_file, str_id, verbose=verbose)
                if ok:
                    print('The task is completed successfully.')
                    return data
                else:
                    raise RuntimeError(f'Bad output: {data}')
            raise RuntimeError(f'Failed in Launching the task with return code {code}.')
        finally:
            if clear_cache and exists_file(json_file):
                try_running(try_fn=lambda: os.remove(json_file), return_try=False)

    @classmethod
    def from_dir(cls, project_path, test: bool = True, injections: List[Tuple[str, BaseInjector]] = None):
        print('Checking the skeleton for this RenPy game...')
        abs_path = os.path.abspath(project_path)

        # check the dir structure
        check_renpy_dir(abs_path)

        # find the project name
        project_name = check_project_name(abs_path)

        # Get the executable python
        executable_path = check_python_exe(abs_path)

        tmp_instance = cls(abs_path, executable_path, project_name)
        print('Injecting our code...')
        injection_chain = [tmp_instance.get_base_injection()]
        if isinstance(injections, list):
            register_injections = []
            for name, injector in injections:
                register_injections.append(tmp_instance.register_injection(name, injector))
            injection_chain += register_injections
        # inject and test
        undo_done = False
        try:
            if call_chain(injection_chain):
                if test:
                    print(f'Trying to launch the game...')
                    # test injection
                    data = tmp_instance.launch_task(None, args=['--test-only'])
                    tmp_instance.set_game_info(data['game_info'])
                    print(f'All done! We have detected the game info: {tmp_instance.game_info}')
                return tmp_instance
            else:
                print('Injection failed! Undo injections...')
                undo_done = True
                undo_chain(injection_chain)
        except Exception as e:
            logging.exception(e)
            if not undo_done:
                undo_chain(injection_chain)
            raise e

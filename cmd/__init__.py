from typing import Any

from cmd.io import new_cmd, old_cmd, savehtml_cmd, loadhtml_cmd, saveexcel_cmd, loadexcel_cmd, dumptoexcel_cmd, \
    updatefromexcel_cmd
from cmd.manage import delete_cmd, list_cmd, clear_cmd
from cmd.project import merge_cmd, apply_cmd, acceptuntrans_cmd, revert_cmd, remove_empty_translation_cmd
from cmd.trans import translate_cmd, dltranslate_cmd

_REGISTERED_CMDS = {
    'new': new_cmd,
    'n': new_cmd,
    'old': old_cmd,
    'o': old_cmd,
    'translate': translate_cmd,
    't': translate_cmd,
    'dltranslate': dltranslate_cmd,
    'dlt': dltranslate_cmd,
    'merge': merge_cmd,
    'm': merge_cmd,
    'apply': apply_cmd,
    'a': apply_cmd,
    'revert': revert_cmd,
    'r': revert_cmd,
    'removeempty': remove_empty_translation_cmd,
    're': remove_empty_translation_cmd,
    'list': list_cmd,
    'l': list_cmd,
    'delete': delete_cmd,
    'd': delete_cmd,
    'clear': clear_cmd,
    'c': clear_cmd,
    'savehtml': savehtml_cmd,
    'sh': savehtml_cmd,
    'loadhtml': loadhtml_cmd,
    'lh': loadhtml_cmd,
    'saveexcel': saveexcel_cmd,
    'se': saveexcel_cmd,
    'loadexcel': loadexcel_cmd,
    'le': loadexcel_cmd,
    'dump': dumptoexcel_cmd,
    'du': dumptoexcel_cmd,
    'update': updatefromexcel_cmd,
    'up': updatefromexcel_cmd,
    'accept': acceptuntrans_cmd,
    'ac': acceptuntrans_cmd,
}


def register_cmd(name: str, cmd_fn: Any):
    assert name is not None and name.strip() != '', f'Command name should be not empty!'
    if name in _REGISTERED_CMDS:
        raise RuntimeError('Existing command name: {name}')
    _REGISTERED_CMDS[name] = cmd_fn


def exists_cmd(name: str):
    return name in _REGISTERED_CMDS


def unregister_cmd(name: str):
    if exists_cmd(name):
        _REGISTERED_CMDS.pop(name)

def execute_cmd(name: str, *args):
    _REGISTERED_CMDS[name](*args)

def all_cmds():
    return list(_REGISTERED_CMDS.keys())

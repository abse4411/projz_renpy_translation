import glob
import os.path
from typing import List

import log.logger
from config.config import default_config, CONFIG_FILE

from prettytable import PrettyTable

from store.index import project_index
from util.file import exists_dir, file_name


def _save_pt(proj: project_index):
    proj.save(os.path.join(default_config.project_path, f'{proj.full_name}.pt'))


def _list_projects():
    return sorted(glob.glob(os.path.join(default_config.project_path, '*.pt')))


def help_cmd():
    print("RenPy rpy文件机翻工具")
    print("By abse4411(Github:https://github.com/abse4411/projz_renpy), version 2.0")
    table = PrettyTable(
        ['Command', 'Usage', 'Help'])
    table.add_row(['new', 'new {tl_path} {name} {tag}',
                   'Create an untranslated index from the translation dir ({tl_path}) in renpy.\n It may be like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as untranslated ones.\n The {name} and {tag} are using while saving.'])
    table.add_row(['old', 'old {tl_path} {name} {tag}',
                   'Create a translated index from the translation dir ({tl_path}) in renpy.\n It may be like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as translated ones.\n The {name} and {tag} are using while saving.'])
    table.add_row(['translate', 'translate {proj_idx} {tran_api}',
                   'Translate all untranslated texts with the given translation API {tran_api} for the project specified by the index {proj_idx}.'])
    table.add_row(['merge', 'merge {sproj_idx} {tproj_idx}',
                   'Merge translated texts from a project {sproj_idx} to the target project {tproj_idx}.'])
    table.add_row(['apply', 'apply {proj_idx} {save_dir}',
                   'Apply all translated texts to rpy file. \nThe  built directory structure is the same as the original project.'])
    table.add_row(['list', 'list',
                   f'list projects in {default_config.project_path}, you can change it in {CONFIG_FILE} - GLOBAL.PROJECT_PATH'])
    table.add_row(['help', 'help', 'Show all available commands.'])
    table.add_row(['quit', 'quit', 'Say goodbye'])
    print(table)


def list_cmd():
    projs = _list_projects()
    print(f'there are {len(projs)} projects in {default_config.project_path}')
    projs = [project_index.load_from_file(p) for p in projs]
    table = PrettyTable(
        ['Index', 'Project', 'Tag', 'Translated line(s)', 'Untranslated line(s)', 'Source dir', 'Num Rpys'])
    for i, p in enumerate(projs):
        table.add_row(
            [i, p.project_name, p.project_tag, p.translation_size, p.untranslation_size, p.source_dir,
             p.num_rpys])
    print(table)


def quit():
    print('Have a nice day! Bye bye! :-)')
    exit(0)


def old_cmd(dir: str, name: str, tag: str):
    assert exists_dir(dir), f'{dir} is not a directory!'
    p = project_index.init_from_dir(dir, name, tag,
                                    is_translated=True)
    _save_pt(p)


def new_cmd(dir: str, name: str, tag: str):
    assert exists_dir(dir), f'{dir} is not a directory!'
    p = project_index.init_from_dir(dir, name, tag,
                                    is_translated=False)
    _save_pt(p)


def merge_cmd(source_idx: int, target_idx: int):
    source_idx, target_idx = int(source_idx), int(target_idx)
    projs = _list_projects()
    sproj, tproj = projs[source_idx], projs[target_idx]
    yes = input(f'Merge all translated texts from {file_name(sproj)} to {file_name(tproj)}? Enter Y/y to continue:')
    if yes.strip().lower() == 'y':
        sproj = project_index.load_from_file(sproj)
        tproj = project_index.load_from_file(tproj)
        tproj.merge_from(sproj)
        _save_pt(tproj)


def translate_cmd(proj_idx, api_name):
    projs = _list_projects()
    proj = project_index.load_from_file(projs[proj_idx])
    pass


def apply_cmd(proj_idx:int):
    projs = _list_projects()
    proj = project_index.load_from_file(projs[int(proj_idx)])
    proj.apply(default_config.project_path)


def main():
    register_commands = {
        'new': new_cmd,
        'old': old_cmd,
        'translate': translate_cmd,
        'merge': merge_cmd,
        'apply': apply_cmd,
        'list': list_cmd,
        'help': help_cmd,
        'quit': quit,
        'q': quit,
        'Q': quit,
    }
    help_cmd()
    while True:
        args = input('What is your next step? (Enter a command or Q/q to exit):')
        args = args.strip()
        args = [c.strip() for c in args.split() if c.strip() != '']
        if len(args) >= 1:
            cmd = args[0].lower()
            if cmd in register_commands:
                try:
                    register_commands[cmd](*args[1:])
                except Exception as e:
                    print(e)
            else:
                print(
                    f'Sorry, it seems to be a invalid command. Available commands are {list(register_commands.keys())}.')
    pass


if __name__ == '__main__':
    main()

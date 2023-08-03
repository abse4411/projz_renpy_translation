import glob
import logging
import os.path
from typing import List

import prettytable

import log.logger
from config.config import default_config, CONFIG_FILE

from prettytable import PrettyTable

from store.html_store import save_to_html, load_from_html
from store.index import project_index
from trans import web_translator
from trans.thread_trans import concurrent_translator
from util.file import exists_dir, file_name, exists_file, mkdir
from util.misc import my_input


def _list_projects():
    return sorted(glob.glob(os.path.join(default_config.project_path, '*.pt')))


def _list_projects_and_select(indexes: List[int]):
    projs = _list_projects()
    res = []
    for i in indexes:
        i = int(i)
        assert 0 <= i < len(projs), f'index {i} out of range, available indexes are:{list(range(len(projs)))}'
        res.append(projs[i])
    return res

def help_cmd():
    print("RenPy rpy文件机翻工具")
    print("By abse4411(Github:https://github.com/abse4411/projz_renpy), version 2.0")
    table = PrettyTable(
        ['Command', 'Usage', 'Help'])
    table.hrules = prettytable.ALL
    table.add_row(['new or n', 'new {tl_path} {name} {tag}',
                   'Create an untranslated index from the translation dir ({tl_path}) in renpy.\n It may be like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as untranslated ones.\n The {name} and {tag} are using while saving.'])
    table.add_row(['old or o', 'old {tl_path} {name} {tag}',
                   'Create a translated index from the translation dir ({tl_path}) in renpy.\n It may be like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as translated ones.\n The {name} and {tag} are using while saving.'])
    table.add_row(['translate or t', 'translate {proj_idx} {tran_api}',
                   'Translate all untranslated texts using the translation API {tran_api} for the project {proj_idx}.\n'
                   'Available translation APIs are caiyu, google, baidu, and youdao.'])
    table.add_row(['merge or m', 'merge {sproj_idx} {tproj_idx}',
                   'Merge translated texts from a project {sproj_idx} to the target project {tproj_idx}.'])
    table.add_row(['apply or a', 'apply {proj_idx}',
                   'Apply all translated texts of project {proj_idx} to rpy file. \nThe  built directory structure is the same as the original project.'
                   f' All files will be save in {default_config.project_path}'])
    table.add_row(['savehtml or sh', 'savehtml {proj_idx} or\nsavehtml {proj_idx} {limit}',
                   'Save untranslated texts of project {proj_idx} to a html file where Edge or Chrome can perform translating.\n'
                   'Please use the Chrome or MS Edge to translate the html file, then save to overwrite it.\n'
                   'The {limit} is optional, or specify it to limit the number of output lines.\n'
                   'After all, use loadhtml {proj_idx} to update translated texts!'])
    table.add_row(['loadhtml or lh', 'loadhtml {proj_idx} {html_file} or\nloadhtml {proj_idx}',
                   'Load translated texts from a translated html file, and apply to untranslated texts of project {proj_idx}.\n'
                   'If the {html_file} is not specified, we will find the corresponding html file for the project {proj_idx} \nat "{PROJECT_PATH}/html/{project.full_name}.html".'])
    table.add_row(['list or l', 'list',
                   f'list projects in {default_config.project_path}, you can change it in {CONFIG_FILE} - GLOBAL.PROJECT_PATH'])
    table.add_row(['help or h', 'help', 'Show all available commands.'])
    table.add_row(['quit or q', 'quit', 'Say goodbye'])
    print(table)


def list_cmd():
    projs = _list_projects()
    print(f'there are {len(projs)} projects in {default_config.project_path}')
    projs = [project_index.load_from_file(p) for p in projs]
    table = PrettyTable(
        ['Project Index', 'Project', 'Tag', 'Translated line(s)', 'Untranslated line(s)', 'Source dir', 'Num Rpys'])
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
    p.save_by_default()


def new_cmd(dir: str, name: str, tag: str):
    assert exists_dir(dir), f'{dir} is not a directory!'
    p = project_index.init_from_dir(dir, name, tag,
                                    is_translated=False)
    p.save_by_default()


def merge_cmd(source_idx: int, target_idx: int):
    source_idx, target_idx = int(source_idx), int(target_idx)
    sproj, tproj = _list_projects_and_select([source_idx, target_idx])
    yes = my_input(f'Merge all translated texts from {file_name(sproj)} to {file_name(tproj)}? Enter Y/y to continue:')
    if yes.strip().lower() == 'y':
        sproj = project_index.load_from_file(sproj)
        tproj = project_index.load_from_file(tproj)
        tproj.merge_from(sproj)
        tproj.save_by_default()


def translate_cmd(proj_idx: int, api_name: str):
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    assert api_name.strip() != '', f'api_name is empty!'
    driver_path = default_config.get_global('CHROME_DRIVER')
    translator_class = web_translator.__dict__[api_name]
    translator = concurrent_translator(proj, lambda: translator_class(driver_path))
    translator.start()
    proj.save_by_default()


def apply_cmd(proj_idx: int):
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    proj.apply(default_config.project_path)


def savehtml_cmd(proj_idx: int, limit: int = None):
    if limit is not None:
        limit = int(limit)
        assert limit > 0, 'limit should be large than 0'
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    save_path = os.path.join(default_config.project_path, 'html')
    mkdir(save_path)
    save_file = os.path.join(save_path, f'{proj.full_name}.html')
    untranslated_lines = proj.untranslated_lines
    if limit is not None:
        untranslated_lines = untranslated_lines[:limit]
    save_to_html(save_file, untranslated_lines)
    logging.info(f'Html file is saved to: {save_file}. Use the Chrome or MS Edge translate it and overwrite it.')


def loadhtml_cmd(proj_idx: int, html_file: str = None):
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    if html_file is None:
        save_path = os.path.join(default_config.project_path, 'html')
        html_file = os.path.join(save_path, f'{proj.full_name}.html')
    else:
        assert exists_file(html_file), f'File {html_file} not found!'
    s, t = load_from_html(html_file, proj.untranslated_lines)
    proj.update(s, t)
    proj.save_by_default()


def main():
    register_commands = {
        'new': new_cmd,
        'n': new_cmd,
        'old': old_cmd,
        'o': old_cmd,
        'translate': translate_cmd,
        't': translate_cmd,
        'merge': merge_cmd,
        'm': merge_cmd,
        'apply': apply_cmd,
        'a': apply_cmd,
        'list': list_cmd,
        'l': list_cmd,
        'savehtml': savehtml_cmd,
        'sh': savehtml_cmd,
        'loadhtml': loadhtml_cmd,
        'lh': loadhtml_cmd,
        'help': help_cmd,
        'h': help_cmd,
        'quit': quit,
        'q': quit,
    }
    help_cmd()
    while True:
        args = my_input('What is your next step? (Enter a command or Q/q to exit): ')
        args = args.strip()
        args = [c.strip() for c in args.split() if c.strip() != '']
        if len(args) >= 1:
            cmd = args[0].lower()
            if cmd in register_commands:
                try:
                    register_commands[cmd](*args[1:])
                except Exception as e:
                    print(f'error: {e}')
            else:
                print(
                    f'Sorry, it seems to be a invalid command. Available commands are {list(register_commands.keys())}.')
    pass


if __name__ == '__main__':
    main()

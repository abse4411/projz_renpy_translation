import glob
import logging
import os.path
from collections import defaultdict
from typing import List

import prettytable

import log.logger
from config.config import default_config, CONFIG_FILE

from prettytable import PrettyTable

from store.fetch import preparse_rpy_file
from store.html_store import save_to_html, load_from_html
from store.index import project_index
from trans import web_translator
from trans.thread_trans import concurrent_translator
from util.file import exists_dir, file_name, exists_file, mkdir
from util.misc import my_input, yes


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
    print("By abse4411(Github:https://github.com/abse4411/projz_renpy), version 3.0")
    table = PrettyTable(
        ['Command', 'Usage', 'Help'])
    table.hrules = prettytable.ALL
    table.add_row(['new or n', 'new {tl_path} {name} {tag}',
                   'Create an untranslated index from the translation dir ({tl_path}) in renpy.\n It may be like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as untranslated ones.\n The {name} and {tag} are using while saving.'])
    table.add_row(['old or o', 'old {tl_path} {name} {tag}',
                   'Create a translated index from the translation dir ({tl_path}) in renpy.\n It may be like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as translated ones.\n The {name} and {tag} are using while saving.'])
    table.add_row(['delete or d', 'delete {proj_idx}', 'Delete the specified project {proj_idx}.'])
    table.add_row(['clear or c', 'clear', f'Clear all projects in {default_config.project_path}.'])
    table.add_row(['translate or t', 'translate {proj_idx} {tran_api} or\ntranslate {proj_idx} {tran_api} {lang}',
                   'Translate all untranslated texts using the translation API {tran_api} for the project {proj_idx}.\n'
                   'The lang {lang} is optional, or specify it to use this language {lang}.\n'
                   'Available translation APIs are caiyu, google, baidu, and youdao.'])
    table.add_row(['merge or m', 'merge {sproj_idx} {tproj_idx} or\nmerge {sproj_idx} {tproj_idx} {lang}',
                   'Merge translated texts from a project {sproj_idx} to the target project {tproj_idx}.\n'
                   'The lang {lang} is optional, or specify it to use this language {lang}.'
                   ])
    table.add_row(['apply or a', 'apply {proj_idx}',
                   'Apply all translated texts of project {proj_idx} to rpy file. \nThe  built directory structure is the same as the original project.'
                   f' All files will be save in {default_config.project_path}'])
    table.add_row(['savehtml or sh', 'savehtml {proj_idx} or\nsavehtml {proj_idx} {lang} {limit}',
                   'Save untranslated texts of project {proj_idx} to a html file where Chrome or Microsoft Edge can perform translating.\n'
                   'Please use the Chrome or Microsoft Edge to translate the html file, then save to overwrite it.\n'
                   'The argument {limit} is optional, or specify it to limit the number of output lines.\n'
                   'The lang {lang} is optional, or specify it to use this language {lang}.\n'
                   'After all, use loadhtml {proj_idx} to update translated texts!'])
    table.add_row(['loadhtml or lh', 'loadhtml {proj_idx} or\nloadhtml {proj_idx} {lang} {html_file}',
                   'Load translated texts from a translated html file, and apply to untranslated texts of project {proj_idx}.\n'
                   'The lang {lang} is optional, or specify it to use this language {lang}.\n'
                   'If the {html_file} is not specified, we will find the corresponding html file for the project {proj_idx} \n'
                   f'at "{default_config.project_path}/html/{{project.full_name}}.html".'])
    table.add_row(['list or l', 'list or list {proj_idx}',
                   f'list projects in {default_config.project_path}, you can change it in {CONFIG_FILE}: [GLOBAL].PROJECT_PATH.\n'
                   'The argument {proj_idx} is optional, or specify it to show detailed info for the project {proj_idx}.\n'])
    table.add_row(['help or h', 'help', 'Show all available commands.'])
    table.add_row(['quit or q', 'quit', 'Say goodbye'])
    print(table)


def list_cmd(proj_idx: int = None):
    if proj_idx is None:
        projs = _list_projects()
        print(f'there are {len(projs)} projects in {default_config.project_path}')
        projs = [project_index.load_from_file(p) for p in projs]
        table = PrettyTable(
            ['Project Index', 'Project', 'Tag', 'Translated line(s)', 'Untranslated line(s)', 'Source dir', 'Num Rpys'])
        table.hrules = prettytable.ALL
        for i, p in enumerate(projs):
            untrans_cnt = '\n'.join([f'{l}: {p.untranslation_size(l)}' for l in p.untranslated_langs])
            trans_cnt = '\n'.join([f'{l}: {p.translation_size(l)}' for l in p.translated_langs])
            table.add_row(
                [i, p.project_name, p.project_tag, trans_cnt, untrans_cnt, p.source_dir,
                 p.num_rpys])
        print(table)
    else:
        proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
        table = PrettyTable(
            ['Project', 'Tag', 'Translated line(s)', 'Untranslated line(s)', 'Source dir', 'Num Rpys'])
        untrans_cnt = '\n'.join([f'{l}: {proj.untranslation_size(l)}' for l in proj.untranslated_langs])
        trans_cnt = '\n'.join([f'{l}: {proj.translation_size(l)}' for l in proj.translated_langs])
        table.add_row(
            [proj.project_name, proj.project_tag, trans_cnt, untrans_cnt, proj.source_dir,
             proj.num_rpys])
        print(table)
        table = PrettyTable(
            ['Rpy file', 'Translated line(s)', 'Untranslated line(s)', 'Invalid line(s)', 'Sum'])
        table.hrules = prettytable.ALL

        def _get_statistics(lang_dict):
            cnt = 0
            lang_arr = []
            for k, v in lang_dict.items():
                lang_arr.append(f'{k}: {len(v)}')
                cnt += len(v)
            return lang_arr, cnt

        def _add(accum, lang_dict):
            for k, v in lang_dict.items():
                accum[k] += v

        tot_trans, tot_untran, tot_invalid = defaultdict(list), defaultdict(list), defaultdict(list)
        for f in proj.rpys:
            trans_dict, untrans_dict, invalid_dict = project_index.rpy_statistics(f)
            (t, tc), (ut, utc), (a, ac) = _get_statistics(trans_dict), _get_statistics(untrans_dict), _get_statistics(
                invalid_dict)
            _add(tot_trans, trans_dict)
            _add(tot_untran, untrans_dict)
            _add(tot_invalid, invalid_dict)
            table.add_row([f, '\n'.join(t), '\n'.join(ut), '\n'.join(a), tc + utc + ac])
        (t, tc), (ut, utc), (a, ac) = _get_statistics(tot_trans), _get_statistics(tot_untran), _get_statistics(
            tot_invalid)
        table.add_row(['Sum', '\n'.join(t), '\n'.join(ut), '\n'.join(a), tc + utc + ac])
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


def merge_cmd(source_idx: int, target_idx: int, lang: str = None):
    source_idx, target_idx = int(source_idx), int(target_idx)
    assert source_idx != target_idx, f'source_idx({source_idx}) should diff from target_idx({target_idx}).'
    sproj, tproj = _list_projects_and_select([source_idx, target_idx])
    if yes(f'Merge all translated texts from {file_name(sproj)} to {file_name(tproj)}?'):
        sproj = project_index.load_from_file(sproj)
        tproj = project_index.load_from_file(tproj)
        tproj.merge_from(sproj, lang)
        tproj.save_by_default()


def translate_cmd(proj_idx: int, api_name: str, lang:str=None):
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    if lang is None:
        lang = proj.first_untranslated_lang
        logging.info(
            f'Selecting the default language {lang} for translating. If you want change to another language, please specify the argument {{lang}}')
    else:
        assert lang in proj.untranslated_langs, f'The selected_lang {lang} is not not Found! Available language(s) are {proj.untranslated_langs}.'
    assert api_name.strip() != '', f'api_name is empty!'
    driver_path = default_config.get_global('CHROME_DRIVER')
    translator_class = web_translator.__dict__[api_name]
    translator = concurrent_translator(proj, lambda: translator_class(driver_path))
    translator.start(lang)
    proj.save_by_default()


def apply_cmd(proj_idx: int, lang: str = None):
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    proj.apply_by_default(lang)


def delete_cmd(proj_idx: int):
    # projs = _list_projects()
    proj = _list_projects_and_select([proj_idx])[0]
    if yes(f'Are your sure to delete {proj}?'):
        os.remove(proj)
        logging.warning(f'{proj} is deleted!')


def clear_cmd():
    projs = _list_projects()
    if len(projs) <= 0:
        print(f'There are not projects in {default_config.project_path}')
    print(f'The following {len(projs)} project(s) will be cleared:')
    for p in projs:
        print(p)
    if yes(f'Are your sure to delete these {len(projs)} project(s)?'):
        for p in projs:
            os.remove(p)
            logging.warning(f'{p} is deleted!')


def savehtml_cmd(proj_idx: int, lang: str = None, limit: int = None):
    if limit is not None:
        limit = int(limit)
        assert limit > 0, 'limit should be large than 0'
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    if lang is None:
        lang = proj.first_untranslated_lang
        logging.info(
            f'Selecting the default language {lang} for savehtml. If you want change to another language, please specify the argument {{lang}}')
    save_path = os.path.join(default_config.project_path, 'html')
    mkdir(save_path)
    save_file = os.path.join(save_path, f'{proj.full_name}.html')
    untranslated_lines = proj.untranslated_lines(lang)
    if limit is not None:
        untranslated_lines = untranslated_lines[:limit]
    save_to_html(save_file, untranslated_lines)
    logging.info(f'Html file is saved to: {save_file}. Use the Chrome or MS Edge translate it and overwrite it.')


def loadhtml_cmd(proj_idx: int, lang: str = None, html_file: str = None):
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    if lang is None:
        lang = proj.first_untranslated_lang
        logging.info(
            f'Selecting the default language {lang} for loadhtml. If you want change to another language, please specify the argument {{lang}}')
    if html_file is None:
        save_path = os.path.join(default_config.project_path, 'html')
        html_file = os.path.join(save_path, f'{proj.full_name}.html')
    else:
        assert exists_file(html_file), f'File {html_file} not found!'
    source_data = proj.untranslated_lines(lang)
    res = load_from_html(html_file, source_data)
    proj.update(res, lang)
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
        'delete': delete_cmd,
        'd': delete_cmd,
        'clear': clear_cmd,
        'c': clear_cmd,
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
                    logging.exception(e)
            else:
                print(
                    f'Sorry, it seems to be a invalid command. Available commands are {list(register_commands.keys())}.')
    pass


if __name__ == '__main__':
    main()

import distutils
import glob
import logging
import os.path
import sys
from collections import defaultdict
from typing import List

import prettytable

import log.logger
from config.config import default_config, CONFIG_FILE

from prettytable import PrettyTable

from store.file_store import save_to_html, load_from_html, load_from_excel, save_to_excel
from store.index import project_index
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
    table.add_row(['new or n', 'new {tl_path} {name} {tag} or\nnew {tl_path} {name} {tag} {greedy=True}',
                   'Create an untranslated index from the translation dir ({tl_path}) in renpy.\n It may like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as untranslated ones.\n The {name} and {tag} are using while saving.]\n'
                   'The argument {greedy} is optional, or specify it by True to scan more translation item,\n'
                   'which also discard less invalid lines. Default as True.'])
    table.add_row(['old or o', 'old {tl_path} {name} {tag}\nnew {tl_path} {name} {tag} {greedy=True}',
                   'Create a translated index from the translation dir ({tl_path}) in renpy.\n It may like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as translated ones.\n The {name} and {tag} are using while saving.\n'
                   'The argument {greedy} is optional, or specify it by True to scan more translation item,\n'
                   'which also discard less invalid lines. Default as True.'])
    table.add_row(['delete or d', 'delete {proj_idx}', 'Delete the specified project {proj_idx}.'])
    table.add_row(['clear or c', 'clear', f'Clear all projects in {default_config.project_path}.'])
    table.add_row(['translate or t', 'translate {proj_idx} {tran_api} or\ntranslate {proj_idx} {tran_api} {num_workers} or\nq'
                                     'translate {proj_idx} {tran_api} {num_workers} {lang}',
                   'Translate all untranslated texts using the translation API {tran_api} for the project {proj_idx}.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'The argument {num_workers=1} is optional, or specify it to set the number of browsers to launch.  Default as 1.\n'
                   'Available translation APIs are caiyu, google, baidu, and youdao.'])
    table.add_row(['dltranslate or dlt', 'dltranslate {proj_idx} {model_name} or\ndltranslate {proj_idx} {model_name} {lang}',
                   'Translate all untranslated texts using the AI translation model {model_name} for the project {proj_idx}.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'Available translation models are m2m100, mbart50, and nllb200.'])
    table.add_row(['merge or m', 'merge {sproj_idx} {tproj_idx} or\nmerge {sproj_idx} {tproj_idx} {lang}',
                   'Merge translated texts from a project {sproj_idx} to the target project {tproj_idx}.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.'
                   ])
    table.add_row(['apply or a', 'apply {proj_idx} or apply {proj_idx} {lang} or\n'
                                 'apply {proj_idx} {lang} {greedy=True}',
                   'Apply all translated texts of project {proj_idx} to rpy files. \nThe  built directory structure is the same as that of the original project.'
                   f' All rpy files will be save in {default_config.project_path}\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'The argument {greedy} is optional, or specify it by True to scan more translation item. Default as True.'])
    table.add_row(['savehtml or sh', 'savehtml {proj_idx} or\nsavehtml {proj_idx} {lang} {limit}',
                   'Save untranslated texts of project {proj_idx} to a html file where Chrome (NOT recommend) or Microsoft Edge can perform translating.\n'
                   'Please use the Chrome or Microsoft Edge to translate the html file, then save to overwrite it.\n'
                   'The argument {limit} is optional, or specify it to limit the number of output lines.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'After all, use loadhtml {proj_idx} to update translated texts!'])
    table.add_row(['loadhtml or lh', 'loadhtml {proj_idx} or\nloadhtml {proj_idx} {lang} {html_file}',
                   'Load translated texts from a translated html file, and apply to untranslated texts of project {proj_idx}.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'If the {html_file} is not specified, we will find the corresponding html file for the project {proj_idx} \n'
                   f'at "{default_config.project_path}/html/{{project.full_name}}.html".'])
    table.add_row(['saveexcel or se', 'saveexcel {proj_idx} or\nsaveexcel {proj_idx} {lang} {limit}',
                   'It works like savehtml, BUT save as an excel file. For augments\' description, please see savehtml.'])
    table.add_row(['loadexcel or le', 'loadexcel {proj_idx} or\nloadexcel {proj_idx} {lang} {excel_file}',
                   'It works like loadhtml, BUT read from an excel file. For augments\' description, please see loadhtml.'])
    table.add_row(['dump', 'dump {proj_idx}',
                   'Dump all translation and untranslation data of project {proj_idx} to an excel file.'])
    table.add_row(['accept or ac', 'accept {proj_idx} or accept {proj_idx} {lang}',
                   'Accept all untranslated texts as translated texts for project {proj_idx}.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.'])
    table.add_row(['list or l', 'list or list {proj_idx}',
                   f'List projects in {default_config.project_path}, you can change it in {CONFIG_FILE}: [GLOBAL].PROJECT_PATH.\n'
                   'The argument {proj_idx} is optional, or specify it to show detailed info for the project {proj_idx}.'])
    table.add_row(['help or h', 'help', 'Show all available commands.'])
    table.add_row(['quit or q', 'quit', 'Say goodbye.'])
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
    sys.exit(0)


def old_cmd(dir: str, name: str, tag: str, greedy: bool = True):
    assert exists_dir(dir), f'{dir} is not a directory!'
    strict_mode = not (distutils.util.strtobool(greedy) if isinstance(greedy, str) else greedy)
    p = project_index.init_from_dir(dir, name, tag,
                                    is_translated=True, strict=strict_mode)
    p.save_by_default()


def new_cmd(dir: str, name: str, tag: str, greedy: bool = True):
    assert exists_dir(dir), f'{dir} is not a directory!'
    strict_mode = not (distutils.util.strtobool(greedy) if isinstance(greedy, str) else greedy)
    p = project_index.init_from_dir(dir, name, tag,
                                    is_translated=False, strict=strict_mode)
    p.save_by_default()

def acceptuntrans_cmd(proj_idx: int, lang: str = None):
    # projs = _list_projects()
    project_name = _list_projects_and_select([proj_idx])[0]
    proj = project_index.load_from_file(project_name)
    if yes(f'Accept all untranslated texts as translated texts for project: {project_name}?'):
        proj.accept_untranslation(lang)
        proj.save_by_default()

def merge_cmd(source_idx: int, target_idx: int, lang: str = None):
    source_idx, target_idx = int(source_idx), int(target_idx)
    assert source_idx != target_idx, f'source_idx({source_idx}) should diff from target_idx({target_idx}).'
    sproj, tproj = _list_projects_and_select([source_idx, target_idx])
    if yes(f'Merge all translated texts from {file_name(sproj)} to {file_name(tproj)}?'):
        sproj = project_index.load_from_file(sproj)
        tproj = project_index.load_from_file(tproj)
        tproj.merge_from(sproj, lang)
        tproj.save_by_default()


def translate_cmd(proj_idx: int, api_name: str, num_workers: int = None, lang: str = None):
    # projs = _list_projects()
    if num_workers is not None:
        num_workers = int(num_workers)
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    if lang is None:
        lang = proj.first_untranslated_lang
        logging.info(
            f'Selecting the default language {lang} for translating. If you want change to another language, please specify the argument {{lang}}')
    else:
        assert lang in proj.untranslated_langs, f'The selected_lang {lang} is not not Found! Available language(s) are {proj.untranslated_langs}.'
    assert api_name.strip() != '', f'api_name is empty!'
    if proj.untranslation_size(lang) <= 0:
        logging.info(f'All texts in {proj.full_name} of language {lang} are translated!')
        return
    driver_path = default_config.get_global('CHROME_DRIVER')
    def save_import():
        try:
            import trans.web
            return trans.web
        except Exception as e:
            logging.exception(e)
        return None
    wt = save_import()
    if wt is not None:
        translator_class = wt.web_translator.__dict__[api_name]
        translator = wt.thread_trans.concurrent_translator(proj, lambda: translator_class(driver_path), num_workers=num_workers)
        translator.start(lang)
        proj.save_by_default()
    else:
        print('To use web translator, please install the package "selenium" (pip install selenium) and download a compatible chrome driver for your chrome brower.\n'
              'You can find chrome drivers in this website: https://chromedriver.storage.googleapis.com/index.html (Version under 116) '
              'or https://googlechromelabs.github.io/chrome-for-testing/#stable (Version 116 or higher).\n'
              'Then config the path of chrome driver in config.ini (CHROME_DRIVER=Your path (chromedriver.exe))')

def dltranslate_cmd(proj_idx: int, model_name: str, lang: str = None):
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    if lang is None:
        lang = proj.first_untranslated_lang
        logging.info(
            f'Selecting the default language {lang} for translating. If you want change to another language, please specify the argument {{lang}}')
    else:
        assert lang in proj.untranslated_langs, f'The selected_lang {lang} is not not Found! Available language(s) are {proj.untranslated_langs}.'
    assert model_name.strip() != '', f'model_name is empty!'
    if proj.untranslation_size(lang) <= 0:
        logging.info(f'All texts in {proj.full_name} of language {lang} are translated!')
        return
    def save_import():
        try:
            import trans.ai
            return trans.ai
        except Exception as e:
            logging.exception(e)
        return None
    wt = save_import()
    if wt is not None:
        assert model_name in wt.AVAILABLE_MODELS, f'model name must be one of {wt.AVAILABLE_MODELS}'
        t = wt.trans_wrapper(proj, model_name)
        t.translate_all(lang)
        proj.save_by_default()
    else:
        print('To use the AI translator, please install these listed package in requirement.txt. (pip install -r requirements.txt)\n'
              'You can also use pytorch with CUDA support to enable faster translation, see: https://pytorch.org/\n')



def apply_cmd(proj_idx: int, lang: str = None, greedy: bool = True):
    # projs = _list_projects()
    strict_mode = not (distutils.util.strtobool(greedy) if isinstance(greedy, str) else greedy)
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    proj.apply_by_default(lang, strict=strict_mode)


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


def saveexcel_cmd(proj_idx: int, lang: str = None, limit: int = None):
    if limit is not None:
        limit = int(limit)
        assert limit > 0, 'limit should be large than 0'
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    if lang is None:
        lang = proj.first_untranslated_lang
        logging.info(
            f'Selecting the default language {lang} for saveexcel. If you want change to another language, please specify the argument {{lang}}')
    save_path = os.path.join(default_config.project_path, 'excel')
    mkdir(save_path)
    save_file = os.path.join(save_path, f'{proj.full_name}.xlsx')
    untranslated_lines = proj.untranslated_lines(lang)
    if limit is not None:
        untranslated_lines = untranslated_lines[:limit]
    save_to_excel(save_file, untranslated_lines)
    logging.info(f'Excel file is saved to: {save_file}.')


def loadexcel_cmd(proj_idx: int, lang: str = None, excel_file: str = None):
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    if lang is None:
        lang = proj.first_untranslated_lang
        logging.info(
            f'Selecting the default language {lang} for loadexcel. If you want change to another language, please specify the argument {{lang}}')
    if excel_file is None:
        save_path = os.path.join(default_config.project_path, 'excel')
        excel_file = os.path.join(save_path, f'{proj.full_name}.xlsx')
    else:
        assert exists_file(excel_file), f'File {excel_file} not found!'
    source_data = proj.untranslated_lines(lang)
    res = load_from_excel(excel_file, source_data)
    proj.update(res, lang)
    proj.save_by_default()


def dumptoexcel_cmd(proj_idx: int):
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    save_path = os.path.join(default_config.project_path, 'excel')
    mkdir(save_path)
    save_file = os.path.join(save_path, f'{proj.full_name}_dump.xlsx')
    proj.dump_to_excel(save_file)


def main():
    register_commands = {
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
        'accept': acceptuntrans_cmd,
        'ac': acceptuntrans_cmd,
        'help': help_cmd,
        'h': help_cmd,
        'quit': quit,
        'q': quit,
    }
    help_cmd()
    while True:
        args = my_input('What is your next step? (Enter a command (case insensitive) or Q/q to exit): ')
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

# package cmd: pyinstaller -i imgs/proz_icon.ico -F parse_console.py --copy-metadata tqdm --copy-metadata regex --copy-metadata requests --copy-metadata packaging --copy-metadata filelock --copy-metadata numpy --copy-metadata tokenizers --copy-metadata huggingface-hub --copy-metadata safetensors --copy-metadata accelerate --copy-metadata pyyaml --copy-metadata sentencepiece
if __name__ == '__main__':
    main()

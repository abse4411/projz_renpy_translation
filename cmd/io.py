import distutils
import logging
import os

from cmd.util import _list_projects_and_select
from config.config import default_config
from store.file_store import save_to_html, load_from_html, save_to_excel, load_from_excel, dump_to_excel, \
    update_from_excel
from store.format import EXPORT_SCOPE
from store.index import project_index
from util.file import exists_dir, mkdir, exists_file


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


def savehtml_cmd(proj_idx: int, lang: str = None, limit: int = None):
    if limit is not None:
        limit = int(limit)
        assert limit > 0, '{limit} should be large than 0'
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    lang = proj.select_or_check_lang(lang, False)
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
    lang = proj.select_or_check_lang(lang, False)
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
        assert limit > 0, '{limit} should be large than 0'
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    lang = proj.select_or_check_lang(lang, False)
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
    lang = proj.select_or_check_lang(lang, False)
    if excel_file is None:
        save_path = os.path.join(default_config.project_path, 'excel')
        excel_file = os.path.join(save_path, f'{proj.full_name}.xlsx')
    else:
        assert exists_file(excel_file), f'File {excel_file} not found!'
    source_data = proj.untranslated_lines(lang)
    res = load_from_excel(excel_file, source_data)
    proj.update(res, lang)
    proj.save_by_default()


def dumptoexcel_cmd(proj_idx: int, lang: str = None, scope: str = EXPORT_SCOPE.ALL):
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    save_path = os.path.join(default_config.project_path, 'excel')
    mkdir(save_path)
    # save_file = os.path.join(save_path, f'{proj.full_name}_dump.xlsx')
    if scope is not None:
        scope = str(scope).lower()
    if scope == EXPORT_SCOPE.TRANS:
        lang = proj.select_or_check_lang(lang, True)
    elif scope == EXPORT_SCOPE.UNTRANS:
        lang = proj.select_or_check_lang(lang, False)
    elif scope == EXPORT_SCOPE.ALL:
        lang = proj.select_or_check_lang(lang, False, assert_existing=False)
        if lang is None:
            lang = proj.select_or_check_lang(lang, True, assert_existing=True)
    save_file = os.path.join(save_path, f'{proj.full_name}_lange_{lang.strip()}.xlsx')
    dump_to_excel(save_file, proj, lang, scope)

def updatefromexcel_cmd(proj_idx: int, lang: str = None, excel_file: str = None):
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    lang = proj.select_or_check_lang(lang, False)
    if excel_file is None:
        save_path = os.path.join(default_config.project_path, 'excel')
        excel_file = os.path.join(save_path, f'{proj.full_name}_lange_{lang.strip()}.xlsx')
    else:
        assert exists_file(excel_file), f'File {excel_file} not found!'
    res = update_from_excel(excel_file, proj, lang)
    proj.update(res, lang, skip_untrans_while_notin=False)
    proj.save_by_default()
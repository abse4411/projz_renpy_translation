import logging
import os
from collections import defaultdict
from functools import cmp_to_key
from typing import List

import tqdm

from store.index import project_index
from store.item import translation_item
from util.file import file_name

class EXPORT_SCOPE:
    TRANS = 'trans'
    UNTRANS = 'untrans'
    ALL = 'all'

class HEAD_NAME:
    INDEX_STR = 'Translation Index (Don\'t modify)'
    RAW_TEXT_STR = 'Raw Text'
    NEW_TEXT_STR = 'Translated Text'
    LANGUAGE_STR = 'Language'
    FILE_STR = 'File'
    LINE_STR = 'Line'
    CODE_INFO_STR = 'Code Info'

def longest_common_prefix(strs:List[str]):
    lcp = ""
    for tmp in zip(*strs):
        if len(set(tmp)) == 1:
            lcp += tmp[0]
        else:
            break
    return lcp

def unpack_items(tran_list: List[translation_item]):
    id_data = []
    la_data = []
    rt_data = []
    nt_data = []
    fi_data = []
    li_data = []
    co_data = []
    for d in tran_list:
        id_data.append(d.identifier)
        la_data.append(d.lang)
        rt_data.append(d.old_str)
        nt_data.append(d.new_str)
        fi_data.append(d.file)
        li_data.append(d.line)
        co_data.append(d.code)
    return {
        HEAD_NAME.INDEX_STR: id_data,
        HEAD_NAME.LANGUAGE_STR: la_data,
        HEAD_NAME.LINE_STR: li_data,
        HEAD_NAME.RAW_TEXT_STR: rt_data,
        HEAD_NAME.NEW_TEXT_STR: nt_data,
        HEAD_NAME.FILE_STR: fi_data,
        HEAD_NAME.CODE_INFO_STR: co_data,
    }
    # return id_data, la_data, rt_data, nt_data, fi_data, li_data, co_data

def group_and_sort(items:List[translation_item]):
    items_dict = defaultdict(list)
    ryp_files = set()
    for item in tqdm.tqdm(items, total=len(items), desc='Scanning the project...'):
        ryp_files.add(item.file)
        items_dict[item.file].append(item)

    sorted_dict = defaultdict(list)
    lcp = longest_common_prefix(list(ryp_files))
    for file in tqdm.tqdm(ryp_files, total=len(ryp_files), desc='Sorting items...'):
        if len(lcp)>=len(file):
            short_name = file_name(file)
        else:
            short_name = file[len(lcp):]
        # replace invalid character (/, :) by the underline:
        short_name = (short_name
                      .replace('/', '_')
                      .replace('\\', '_')
                      .replace(':', '_'))
        arr = items_dict[file]
        arr.sort(key=lambda x: x.line)
        sorted_dict[short_name] = arr
    return sorted_dict


def group_by_file(proj: project_index, lang: str=None, scope: str = EXPORT_SCOPE.ALL):
    item_list = []
    if scope == EXPORT_SCOPE.TRANS:
        proj.check_lang(lang, True)
        item_list += proj.raw_translated_items(lang)
    elif scope == EXPORT_SCOPE.UNTRANS:
        proj.check_lang(lang, False)
        item_list += proj.raw_untranslated_items(lang)
    elif scope == EXPORT_SCOPE.ALL:
        if lang in proj.untranslated_langs:
            item_list += proj.raw_untranslated_items(lang)
        if lang in proj.translated_langs:
            item_list += proj.raw_translated_items(lang)
    else:
        raise ValueError(scope)
    if len(item_list) == 0:
        return lang, []
    return lang, group_and_sort(item_list)




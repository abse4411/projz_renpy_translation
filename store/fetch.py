import logging
import re
from typing import List, Tuple

from tqdm import tqdm

from config.config import default_config
from store.item import translation_item, i18n_translation_dict
from util.misc import text_type, TEXT_TYPE, is_empty, VAR_NAME

# 匹配原始这种格式的符串:"# renpy/common/00accessibility.rpy:138"
regex_code = re.compile(r'^# (.+(?=\.rpy)\.rpy):(\d+)$')
# 匹配字符串这种格式的字符串:"translate chinese nikiinvite2_442941ca_1:"
regex_trans = re.compile(r'^translate (\S+) ([^:]+):$')

TEXT_TYPE_TRANS_ID = "TRANS_ID"
TEXT_TYPE_TRANS_CODE = "TRANS_CODE"


def safely_add_prefix(new_str):
    if new_str is not None and not (new_str.startswith('@$') or new_str.startswith('@@')):
        return '@$' + new_str
    return new_str

def safely_remove_prefix(new_str):
    if new_str is not None and (new_str.startswith('@$') or new_str.startswith('@@')):
        return new_str[len('@$'):]
    return new_str

def get_trans_info(text):
    if text:
        text = text.strip()
        if text != '':
            res = regex_code.match(text)
            if res: return f'{res.group(1)}:{ res.group(2)}', TEXT_TYPE_TRANS_CODE
            res = regex_trans.match(text)
            if res: return (res.group(1), res.group(2)), TEXT_TYPE_TRANS_ID
    return None, None

def determine_new_line(info_dict:dict, in_group=False, strict=False):
    '''
    determine whether a new line is a valid translation_item or not
    :param info_dict: all info about the translation
    :param in_group: indicates an in-group translation line
    :param strict: use strict rule to determine
    :param verbose: indicates logging
    :return:
    '''
    raw_text = info_dict['raw_text']
    raw_line = info_dict['raw_line']
    raw_var = info_dict['raw_var']
    id_data = info_dict['id_data']
    id_line = info_dict['id_line']
    code_data = info_dict['code_data']
    code_line = info_dict['code_line']
    new_text = info_dict['new_text']
    new_line = info_dict['new_line']
    new_var = info_dict['new_var']
    rpy_file = info_dict['rpy_file']

    if id_data is None: return None
    if in_group:
        lang, _ = id_data
        ''' EXAMPLE:
        translate chinese strings:
        
            # renpy/common/00accessibility.rpy:28 <---[code_line]
            old "Self-voicing disabled." <---[raw_line]
            new "Self-voicing disabled."  <---[current line] (i)
        '''
        # if ((raw_var != new_var and (raw_var != VAR_NAME.OLD or new_var != VAR_NAME.NEW))
        #         or (raw_var == new_var and raw_var is None)
        #         or id_line >= raw_line):
        #     return None
        if raw_var != VAR_NAME.OLD or new_var != VAR_NAME.NEW or id_line >= raw_line: return None
        if strict:
            if code_data is not None and code_line + 1 == raw_line and raw_text is not None and raw_line + 1 == new_line:
                return translation_item(
                        old_str=raw_text,
                        new_str=new_text,
                        file=rpy_file,
                        line=new_line,
                        lang=lang,
                        code=code_data,
                        identifier=raw_text
                    )
        else:
            if raw_text is not None and raw_line < new_line:
                return translation_item(
                        old_str=raw_text,
                        new_str=new_text,
                        file=rpy_file,
                        line=new_line,
                        lang=lang,
                        code=code_data if code_data is not None and code_line<raw_line else None,
                        identifier=raw_text
                    )
    else:
        lang, tid = id_data
        ''' EXAMPLE:
        # game/AmiEvents.rpy:39 <---[code_line]
        translate chinese amiinvitegen_2a2264b4: <---[id_line]

            # a "What’s up?" # <---[raw_line]
            a "What’s up?" # <---[current line] (i)
        '''
        if raw_var != new_var: return None
        if strict:
            if code_data is not None and code_line + 1 == id_line \
                    and id_line + 2 == raw_line \
                    and raw_text is not None and raw_line + 1 == new_line:
                return translation_item(
                        old_str=raw_text,
                        new_str=new_text,
                        file=rpy_file,
                        line=new_line,
                        lang=lang,
                        code=code_data,
                        identifier=tid
                    )
        else:
            if id_line < raw_line \
                    and raw_text is not None and raw_line < new_line:
                return translation_item(
                        old_str=raw_text,
                        new_str=new_text,
                        file=rpy_file,
                        line=new_line,
                        lang=lang,
                        code=code_data if code_data is not None and code_line<id_line else None,
                        identifier=tid
                    )
    return None

def preparse_rpy_file(rpy_file, strict=False, verbose=True) -> Tuple[i18n_translation_dict, List[translation_item]]:
    with open(rpy_file, 'r', encoding='utf-8') as f:
        temp_data = f.readlines()
    raw_var = None
    raw_text = None
    raw_line = -1
    id_data = None
    id_line = -1
    code_data = None
    code_line = -1
    valid_cnt = 0
    invalid_cnt = 0

    renpy_keywords = default_config.keywords
    # not under 'translate chinese string'-like group block
    in_group = False
    store = i18n_translation_dict()
    invalid_list = []
    for i, line in enumerate(temp_data, 1):
        line = line.strip()
        if line == '': continue
        text, ttype, var_name = text_type(line)
        if ttype == TEXT_TYPE.RAW and var_name not in renpy_keywords:
            raw_text = text
            if is_empty(text) and verbose:
                logging.warning(f'{rpy_file}[L{i}]: The old text({text}) is empty')
            raw_line = i
            raw_var = var_name
        elif ttype == TEXT_TYPE.NEW and var_name not in renpy_keywords:
            if is_empty(text) and verbose:
                logging.warning(f'{rpy_file}[L{i}]: The new text({text}) is empty!')
            info_dict = {
                'raw_text' : raw_text,
                'raw_line' : raw_line,
                'raw_var' : raw_var,
                'id_data' : id_data,
                'id_line' : id_line,
                'code_data' : code_data,
                'code_line' : code_line,
                'new_text' : text,
                'new_line' : i,
                'new_var' : var_name,
                'rpy_file' : rpy_file,
            }
            if in_group:
                if id_data is not None:
                    lang = id_data[0]
                else:
                    lang = None
                tid = raw_text
                res = determine_new_line(info_dict, in_group, strict)
                if res is not None:
                    if verbose and (lang, tid) in store:
                        old_item = store[(lang, tid)]
                        logging.warning(
                            f'{rpy_file}[L{i}]: Duplicate translation (identifier:{tid}, text:{raw_text}) is found! This may result in error in renpy.\n'
                            f'\tDetailed info:\n'
                            f'\told:{old_item}')
                    store[(lang, tid)] = res
                    valid_cnt += 1
                else:
                    if verbose:
                        logging.warning(f'{rpy_file}[L{i}] Unmatched in-group new text({text}), it will be skipped!')
                    invalid_cnt += 1
                    invalid_list.append(translation_item(
                        old_str = raw_text,
                        new_str = text,
                        file = rpy_file,
                        line = i,
                        lang = lang,
                        code = code_data if code_line<raw_line else None,
                        identifier = raw_text
                    ))
            else:
                if id_data is not None:
                    lang, tid = id_data
                else:
                    lang, tid = None, None
                res = determine_new_line(info_dict, in_group, strict)
                if res is not None:
                    lang, tid = id_data
                    if verbose and (lang, tid) in store:
                        old_item = store[(lang, tid)]
                        logging.warning(
                            f'{rpy_file}[L{i}]: Duplicate translation (identifier:{tid}, text:{raw_text}) is found! This may result in error in renpy.\n'
                            f'\tDetailed info:\n'
                            f'\told:{old_item}')
                    store[(lang, tid)] = res
                    valid_cnt += 1
                else:
                    if verbose:
                        logging.warning(f'{rpy_file}[L{i}] Unmatched not-in-group new text({text}), it will be skipped!')
                    invalid_cnt += 1
                    invalid_list.append(translation_item(
                        old_str = raw_text,
                        new_str = text,
                        file = rpy_file,
                        line = i,
                        lang = lang,
                        code = code_data if code_line<id_line else None,
                        identifier = tid
                    ))
                id_data = None
                id_line = -1
            raw_var = None
            raw_text = None
            raw_line = -1
            code_data = None
            code_line = -1
        else:
            data, ttype = get_trans_info(line)
            if ttype == TEXT_TYPE_TRANS_ID:
                id_data = data
                id_line = i
                if id_data[1] == 'strings':
                    in_group = True
                else:
                    in_group = False
                raw_var = None
                raw_text = None
                raw_line = -1
            elif ttype == TEXT_TYPE_TRANS_CODE:
                code_data = data
                code_line = i
    if verbose:
        logging.info(
            f'{rpy_file}: {valid_cnt} line(s) are added. Other {invalid_cnt} line(s) are skipped!')
    return store, invalid_list


def update_translated_lines_new(rpy_file: str, translated_lines: i18n_translation_dict, strict=False):
    new_i18n_dict, discard_list = preparse_rpy_file(rpy_file, strict=strict)
    # collect some translated items without raw text from discarded items if not in strict mode
    if not strict:
        ''' we collect translated items like:
        # game/AmiEvents.rpy:39 <---[code_line], dispensable
        translate chinese amiinvitegen_2a2264b4: <---[id_line], necessary

            # a "What’s up?" # <---[raw_line], dispensable
            a "What’s up?" # <---[current line] (i), necessary
        '''
        for item in discard_list:
            # not in-group translation
            if item.identifier != item.old_str and item.old_str is None\
                    and item.identifier is not None and item.new_str is not None \
                    and item.new_str != '' and item.lang is not None:
                item.new_str = safely_add_prefix(item.new_str)
                if (item.lang, item.identifier) not in new_i18n_dict:
                    new_i18n_dict[(item.lang, item.identifier)] = item
                else:
                    logging.warning(
                        f'{rpy_file}[L{item.line}]: Duplicate translation (identifier:{item.identifier}, text:{item.new_str}) is found!\n'
                        f'\tDetailed info:\n'
                        f'\told:{new_i18n_dict[(item.lang, item.identifier)]}')

    for lang in new_i18n_dict.langs():
        new_dict = new_i18n_dict[lang]
        if lang in translated_lines:
            old_dict = translated_lines[lang]
            for tid, new_item in new_dict.items():
                line = new_item.line
                new_item.new_str = safely_add_prefix(new_item.new_str)
                if tid in old_dict:
                    old_item = old_dict[tid]
                    logging.warning(
                        f'{rpy_file}[L{line}]: Duplicate translation identifier({tid}) is found! This may result in error in renpy.'
                        f' The old translation({old_item.new_str}) for "{new_item.old_str}" will replace by "{new_item.new_str}"\n.'
                        f'\tDetailed info:\n'
                        f'\told:{old_item}\n'
                        f'\tnew:{new_item}')
                old_dict[tid] = new_item
        else:
            for tid, new_item in new_dict.items():
                new_item.new_str = safely_add_prefix(new_item.new_str)
                translated_lines[(lang, tid)] = new_item

def update_untranslated_lines_new(rpy_file: str, translated_lines: i18n_translation_dict, strict=False):
    new_i18n_dict = preparse_rpy_file(rpy_file, strict=strict)[0]
    for lang in new_i18n_dict.langs():
        new_dict = new_i18n_dict[lang]
        if lang in translated_lines:
            old_dict = translated_lines[lang]
            for tid, new_item in new_dict.items():
                line = new_item.line
                if new_item.new_str != new_item.old_str:
                    logging.warning(f'{rpy_file}[L{line}]: The new text({new_item.new_str}) is not the same as the old text({new_item.old_str})! It will be ignored for translation.')
                    continue
                if tid in old_dict:
                    old_item = old_dict[tid]
                    logging.warning(
                        f'{rpy_file}[L{line}]: Duplicate translation identifier({tid}) is found! This may result in error in renpy.'
                        f' Replacing old translation item with new one.\n'
                        f'\tDetailed info:\n'
                        f'\told:{old_item}\n'
                        f'\tnew:{new_item}')
                new_item.new_str = None
                old_dict[tid] = new_item
        else:
            for tid, new_item in new_dict.items():
                if new_item.new_str != new_item.old_str:
                    logging.warning(f'{rpy_file}[L{new_item.line}]: The new text({new_item.new_str}) is not the same as the old text({new_item.old_str})! It will be ignored for translation.')
                    continue
                new_item.new_str = None
                translated_lines[(lang, tid)] = new_item


if __name__ == '__main__':
    import log.logger
    # print(regex_trans.search('translate chinese jumpymenu3_a439b59a:').groups())
    # print(regex_code.search('# game/AyaneEvents.rpy:584').groups())
    old_rpy_file = r'fc_res/old/script.rpy'
    new_rpy_file = r'fc_res/new/script.rpy'
    # res = preparse_rpy_file(old_rpy_file, False)[0]
    store = i18n_translation_dict()
    update_translated_lines_new(old_rpy_file, store, strict=False)
    def print_dict(res_dict):
        for k, v in res_dict.items():
            print(f'lang:{k}===========================================================>', flush=True)
            for str_id, d in v.items():
                # print(d, flush=True)
                print(d.identifier)
                print(f'\tRAW:[{d.old_str}]')
                print(f'\tNEW:[{d.new_str}]')
                print(f'\tLINE:[{d.line}]')
                print(f'\tCODE:[{d.code}]')
    print_dict(store)
    # old_data = preparse_rpy_file(new_rpy_file)
    # new_data = preparse_rpy_file(new_rpy_file)
    print('********************************************************************', flush=True)
    # print()
    # empty = i18n_translation_dict()
    # update_translated_lines_new(new_rpy_file, res)
    # print_dict(res)
    pass

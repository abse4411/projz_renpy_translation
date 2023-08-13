import logging
import re
from typing import List, Tuple

from tqdm import tqdm

from store.item import translation_item, i18n_translation_dict
from util.misc import text_type, TEXT_TYPE, is_empty

# 匹配原始这种格式的符串:"# renpy/common/00accessibility.rpy:138"
regex_code = re.compile(r'^# (.+(?=\.rpy)\.rpy):(\d+)')
# 匹配字符串这种格式的字符串:"translate chinese nikiinvite2_442941ca_1:"
regex_trans = re.compile(r'^translate (\S+) ([^:]+):')

TEXT_TYPE_TRANS_ID = "TRANS_ID"
TEXT_TYPE_TRANS_CODE = "TRANS_CODE"


def get_trans_info(text):
    if text:
        text = text.strip()
        if text != '':
            res = regex_code.match(text)
            if res: return (res.group(1), res.group(2)), TEXT_TYPE_TRANS_CODE
            res = regex_trans.match(text)
            if res: return (res.group(1), res.group(2)), TEXT_TYPE_TRANS_ID
    return None, None


def preparse_rpy_file(rpy_file, verbose=True) -> Tuple[i18n_translation_dict, List[translation_item]]:
    with open(rpy_file, 'r', encoding='utf-8') as f:
        temp_data = f.readlines()
    raw_text = None
    raw_line = -1
    id_data = None
    id_line = -1
    code_data = None
    code_line = -1
    valid_cnt = 0
    invalid_cnt = 0

    # not under 'translate chinese string'-like group block
    in_group = False
    store = i18n_translation_dict()
    invalid_list = []
    for i, line in enumerate(temp_data, 1):
        line = line.strip()
        if line == '': continue
        text, ttype = text_type(line)
        if ttype == TEXT_TYPE.RAW:
            raw_text = text
            if is_empty(text) and verbose:
                logging.warning(f'{rpy_file}[L{i}]: The old text({text}) is empty')
            raw_line = i
        elif ttype == TEXT_TYPE.NEW:
            if is_empty(text) and verbose:
                logging.warning(f'{rpy_file}[L{i}]: The new text({text}) is empty!')
            if in_group:
                lang, _ = id_data
                ''' EXAMPLE:
                    # renpy/common/00accessibility.rpy:28 <---[code_line]
                    old "Self-voicing disabled." <---[raw_line]
                    new "Self-voicing disabled."  <---[current line] (i)
                '''
                if code_data is not None and code_line + 1 == raw_line and raw_text is not None and raw_line + 1 == i:
                    if verbose and (lang, raw_text) in store:
                        old_item = store[(lang, raw_text)]
                        logging.warning(
                            f'{rpy_file}[L{i}]: Duplicate translation (identifier:{raw_text}, text:{raw_text}) is found! This may result in error in renpy.'
                            f'\tDetailed info:\n'
                            f'\told:{old_item}')
                    store[(lang, raw_text)] = translation_item(
                        old_str=raw_text,
                        new_str=text,
                        file=rpy_file,
                        line=i,
                        lang=lang,
                        code=code_data,
                        identifier=raw_text
                    )
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
                        code = code_data,
                        identifier = raw_text
                    ))
            else:
                ''' EXAMPLE:
                # game/AmiEvents.rpy:39 <---[code_line]
                translate chinese amiinvitegen_2a2264b4: <---[id_line]
                
                    # a "What’s up?" # <---[raw_line]
                    a "What’s up?" # <---[current line] (i)
                '''
                if code_data is not None and code_line + 1 == id_line \
                        and id_data is not None and id_line + 2 == raw_line \
                        and raw_text is not None and raw_line + 1 == i:
                    lang, tid = id_data
                    if verbose and (lang, tid) in store:
                        old_item = store[(lang, tid)]
                        logging.warning(
                            f'{rpy_file}[L{i}]: Duplicate translation (identifier:{tid}, text:{raw_text}) is found! This may result in error in renpy.'
                            f'\tDetailed info:\n'
                            f'\told:{old_item}')
                    store[(lang, tid)] = translation_item(
                        old_str=raw_text,
                        new_str=text,
                        file=rpy_file,
                        line=i,
                        lang=lang,
                        code=code_data,
                        identifier=tid
                    )
                    id_data = None
                    id_line = -1
                    valid_cnt += 1
                else:
                    if verbose:
                        logging.warning(f'{rpy_file}[L{i}] Unmatched not-in-group new text({text}), it will be skipped!')
                    invalid_cnt += 1
                    if id_data is not None:
                        lang, tid = id_data
                    else:
                        lang, tid = None, None
                    invalid_list.append(translation_item(
                        old_str = raw_text,
                        new_str = text,
                        file = rpy_file,
                        line = i,
                        lang = lang,
                        code = code_data,
                        identifier = tid
                    ))
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
            elif ttype == TEXT_TYPE_TRANS_CODE:
                code_data = data
                code_line = i
    if verbose:
        logging.info(
            f'{rpy_file}: {valid_cnt} line(s) are added. Other {invalid_cnt} line(s) are skipped!')
    return store, invalid_list


def update_translated_lines_new(rpy_file: str, translated_lines: i18n_translation_dict):
    new_i18n_dict = preparse_rpy_file(rpy_file)[0]
    for lang in new_i18n_dict.langs():
        new_dict = new_i18n_dict[lang]
        if lang in translated_lines:
            old_dict = translated_lines[lang]
            for tid, new_item in new_dict.items():
                line = new_item.line
                new_item.new_str = '@$' + new_item.new_str
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
                new_item.new_str = '@$' + new_item.new_str
                translated_lines[(lang, tid)] = new_item

def update_untranslated_lines_new(rpy_file: str, translated_lines: i18n_translation_dict):
    new_i18n_dict = preparse_rpy_file(rpy_file)[0]
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
                    new_item.new_str = None
                    logging.warning(
                        f'{rpy_file}[L{line}]: Duplicate translation identifier({tid}) is found! This may result in error in renpy.'
                        f' Replacing old translation item with new one.\n'
                        f'\tDetailed info:\n'
                        f'\told:{old_item}\n'
                        f'\tnew:{new_item}')
                old_dict[tid] = new_item
        else:
            for tid, new_item in new_dict.items():
                if new_item.new_str != new_item.old_str:
                    logging.warning(f'{rpy_file}[L{new_item.line}]: The new text({new_item.new_str}) is not the same as the old text({new_item.old_str})! It will be ignored for translation.')
                    continue
                new_item.new_str = None
                translated_lines[(lang, tid)] = new_item


def update_translated_lines(rpy_file, translated_lines):
    with open(rpy_file, 'r', encoding='utf-8') as f:
        temp_data = f.readlines()
    raw_text = None
    raw_line = -1
    save_cnt = 0
    unsave_cnt = 0
    for i, line in enumerate(temp_data, 1):
        text, ttype = text_type(line)
        if ttype == TEXT_TYPE.RAW:
            if is_empty(text):
                logging.warning(f'{rpy_file}[L{i}]: The old text({text}) is empty')
            raw_text = text
            raw_line = i
        if ttype == TEXT_TYPE.NEW:
            if raw_text is None or i - raw_line != 1:
                logging.error(f'{rpy_file}[L{i}]: Unmatched new text({text}), it will be skipped!')
                raw_text = None
                raw_line = -1
                unsave_cnt += 1
                continue
            if is_empty(text):
                logging.warning(f'{rpy_file}[L{i}]: The new text({text}) is empty!')
            if raw_text in translated_lines:
                tline = translated_lines[raw_text]
                logging.warning(
                    f'{rpy_file}[L{i}]: The old translation({tline.new_str}) for "{raw_text}" will replace by “{text}”. This may result in error in renpy.')
                tline.new_str = '@$' + text
            else:
                translated_lines[raw_text] = translation_item(
                    old_str=raw_text,
                    new_str='@$' + text,
                    file=rpy_file,
                    line=i
                )
            save_cnt += 1
            raw_text = None
            raw_line = -1
    logging.info(
        f'{rpy_file}: {save_cnt} untranslated line(s) are added. Other {unsave_cnt} untranslated line(s) are skipped!')


def update_untranslated_lines(rpy_file, untranslated_lines):
    with open(rpy_file, 'r', encoding='utf-8') as f:
        temp_data = f.readlines()
    raw_text = None
    raw_line = -1
    save_cnt = 0
    unsave_cnt = 0
    for i, line in enumerate(temp_data, 1):
        text, ttype = text_type(line)
        if ttype == TEXT_TYPE.RAW:
            if is_empty(text):
                logging.warning(f'{rpy_file}[L{i}]: The old text({text}) is empty.')
            raw_text = text
            raw_line = i
        if ttype == TEXT_TYPE.NEW:
            if raw_text is None or i - raw_line != 1:
                # logging.info(f'{rpy_file}[L{i}]: Unmatched new text({text}). It is ok, noting that the new text and the old new text must be in pair while getting translated texts.')
                logging.warning(f'{rpy_file}[L{i}]: Unmatched new text({text}). It will be ignored！.')
                # untranslated_lines[text] = translation_item(
                #     old_str=text,
                #     new_str=None,
                #     file=rpy_file,
                #     line=i
                # )
                unsave_cnt += 1
                raw_text = None
                raw_line = -1
                continue
            if raw_text == text:
                if raw_text in untranslated_lines:
                    untline = untranslated_lines[raw_text]
                    logging.warning(
                        f'{rpy_file}[L{i}]: The duplicate untranslated text({raw_text}) is found! This may result in error in renpy.')
                    untline.new_str = text
                else:
                    untranslated_lines[raw_text] = translation_item(
                        old_str=raw_text,
                        new_str=None,
                        file=rpy_file,
                        line=i
                    )
                save_cnt += 1
            else:
                logging.warning(
                    f'{rpy_file}[L{i}]: The new text({text}) is not the same as the old text({raw_text})! It will be ignored for translation.')
                unsave_cnt += 1
            raw_text = None
            raw_line = -1
    logging.info(
        f'{rpy_file}: {save_cnt} untranslated line(s) are added. Other {unsave_cnt} untranslated line(s) are skipped!')




if __name__ == '__main__':
    import log.logger
    # print(regex_trans.search('translate chinese jumpymenu3_a439b59a:').groups())
    # print(regex_code.search('# game/AyaneEvents.rpy:584').groups())
    old_rpy_file = r'fc_res/old/script.rpy'
    new_rpy_file = r'fc_res/new/script.rpy'
    res = preparse_rpy_file(old_rpy_file)[0]
    def print_dict(res_dict):
        for k, v in res_dict.items():
            print(f'lang:{k}===========================================================>', flush=True)
            for d in v.items():
                print(d, flush=True)
    print_dict(res)
    # old_data = preparse_rpy_file(new_rpy_file)
    # new_data = preparse_rpy_file(new_rpy_file)
    print('********************************************************************', flush=True)
    # print()
    empty = i18n_translation_dict()
    update_translated_lines_new(new_rpy_file, res)
    print_dict(res)
    pass

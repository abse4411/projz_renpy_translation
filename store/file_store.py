import hashlib
import logging
import os
from typing import List, Tuple

from pandas import ExcelWriter
import tqdm

from config.config import default_config
from store.format import group_by_file, HEAD_NAME, unpack_items
from store.index import project_index
import pandas as pd

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    <table>
        <tbody>
            <tr>
                <th>Raw Text</th>
            </tr>
{filler}
        </tbody>
    </table>
</body>
</html>
'''
TR_TEMPLATE = '<!--{id}S#2##E3#{text}--><tr><td>B4@# {text}</td></tr>\n'
MAGIC_NUMBER = 78945621384


def my_hash(text: str):
    byte_arr = text.encode('utf-8')
    t = MAGIC_NUMBER
    for b in byte_arr:
        t = ((-t << 1) + 2 * b) ^ b
    if t < 0: t = -t
    return t


def text_id(text):
    md5_str = hashlib.md5(text.encode('utf-8')).hexdigest()
    hash_str = hex(my_hash(text))
    return (md5_str + hash_str).upper()


def save_to_html(file_name: str, tids_and_untranslated_texts: List[Tuple[str, str]]):
    tr_arr = []
    for tid, raw_text in tids_and_untranslated_texts:
        tr_arr.append(TR_TEMPLATE.format(id=text_id(tid), text=raw_text))
    save_html = HTML_TEMPLATE.format(filler=''.join(tr_arr))
    with open(file_name, 'w', encoding='utf-8', newline='\n') as f:
        f.write(save_html)
    logging.info(f'Save untranslated {len(tids_and_untranslated_texts)} translations to {file_name}')


def load_from_html(file_name: str, tids_and_untranslated_texts: List[Tuple[str, str]]):
    unmap = dict()
    use_cnt = 0
    unuse_cnt = 0
    with open(file_name, 'r', encoding='utf-8') as f:
        i = 0
        for l in f:
            i += 1
            l = l.strip()
            if l.startswith('<!--') and l.endswith('</td></tr>'):
                tli, tri = l.find('<!--'), l.find('S#2#')
                nli, nri = l.find('>B4@#'), l.rfind('</td></tr>')
                oli, ori = l.find('#E3#'), l.find('--><tr><td')
                if not (0<=tli<tri and tri<oli<ori and ori<nli<nri):
                    logging.info(f'[Line {i}] Skipping unmatch line:{l}')
                    continue
                encrypted_tid = l[tli + 4:tri].strip().upper()
                new_str = l[nli + 5:nri].strip()
                old_str = l[oli + 4:ori].strip()
                if encrypted_tid == '' or new_str == '' or old_str == '' or new_str == old_str:
                    logging.info(f'[Line {i}] Skipping corrupted translation for raw_text({old_str}) and translated_text({new_str})')
                else:
                    unmap[encrypted_tid] = new_str
    logging.info(f'Found {len(unmap)} translations in {file_name}')
    res = []
    for tid, raw_text in tids_and_untranslated_texts:
        encrypted_tid = text_id(tid)
        if encrypted_tid in unmap:
            if raw_text is not None and raw_text.strip() == unmap[encrypted_tid]:
                logging.info(f'Skipping corrupted translation: "{raw_text}" for raw_text({raw_text})==translated_text({unmap[encrypted_tid]})')
                unuse_cnt += 1
            else:
                res.append((tid, '@@'+unmap[encrypted_tid]))
                use_cnt += 1
        else:
            logging.warning(f'Untranslated text (Translation ID: {tid}, text: {raw_text}) found, it will be ignored!')
            unuse_cnt += 1
    logging.info(f'There are {use_cnt} translated line(s) and {unuse_cnt} untranslated line(s) in {file_name}')
    return res

def save_to_excel(file_name: str, tids_and_untranslated_texts: List[Tuple[str, str]]):
    columns = [HEAD_NAME.INDEX_STR, HEAD_NAME.NEW_TEXT_STR]
    excel_id_data = []
    excel_nt_data = []
    for tid, raw_text in tids_and_untranslated_texts:
        excel_id_data.append(text_id(tid))
        excel_nt_data.append(raw_text)
    df = pd.DataFrame({HEAD_NAME.INDEX_STR:excel_id_data,
                  HEAD_NAME.NEW_TEXT_STR:excel_nt_data})
    df = df.reindex(columns=columns)
    df.to_excel(file_name, index=False)
    logging.info(f'Save untranslated {len(tids_and_untranslated_texts)} translations to {file_name}')


def load_from_excel(file_name: str, tids_and_untranslated_texts: List[Tuple[str, str]]):
    unmap = dict()
    use_cnt = 0
    unuse_cnt = 0
    df = pd.read_excel(file_name, na_filter=False,
                       header=None,
                       skiprows=[0],
                       usecols=[0, 1],
                       names=[HEAD_NAME.INDEX_STR, HEAD_NAME.NEW_TEXT_STR])
    i = 0
    for encrypted_tid, new_str in zip(df[HEAD_NAME.INDEX_STR], df[HEAD_NAME.NEW_TEXT_STR]):
        encrypted_tid, new_str = str(encrypted_tid).strip().upper(), str(new_str).strip()
        if encrypted_tid == '' or new_str == '':
            logging.info(f'[Line {i}] Skipping corrupted translation for translated_text({new_str})')
        else:
            unmap[encrypted_tid] = new_str
    logging.info(f'Found {len(unmap)} translations in {file_name}')
    res = []
    for tid, raw_text in tids_and_untranslated_texts:
        encrypted_tid = text_id(tid)
        if encrypted_tid in unmap:
            if raw_text is not None and raw_text.strip() == unmap[encrypted_tid]:
                logging.info(f'Skipping corrupted translation: "{raw_text}" for raw_text({raw_text})==translated_text({unmap[encrypted_tid]})')
                unuse_cnt += 1
            else:
                res.append((tid, '@@'+unmap[encrypted_tid]))
                use_cnt += 1
        else:
            logging.warning(f'Untranslated text (Translation ID: {tid}, text: {raw_text}) found, it will be ignored!')
            unuse_cnt += 1
    logging.info(f'There are {use_cnt} translated line(s) and {unuse_cnt} untranslated line(s) in {file_name}')
    return res


def dump_to_excel(save_file:str, proj: project_index, lang: str, scope: str):
    columns = [HEAD_NAME.INDEX_STR, HEAD_NAME.LANGUAGE_STR, HEAD_NAME.LINE_STR, HEAD_NAME.RAW_TEXT_STR, HEAD_NAME.NEW_TEXT_STR,
              HEAD_NAME.CODE_INFO_STR, HEAD_NAME.FILE_STR]
    lang, sorted_data = group_by_file(proj, lang, scope)
    if lang is None or len(sorted_data) == 0:
        logging.info(f'Not translation or untranslation data ({lang}) in the current project')
        return
    cnt = 0
    with ExcelWriter(save_file) as writer:
        for file, data in tqdm.tqdm(sorted_data.items(), total=len(sorted_data), desc='Saving to file...'):
            df = pd.DataFrame(unpack_items(data))
            cnt += len(df)
            df = df.reindex(columns=columns)
            df.to_excel(writer, sheet_name=file.strip(), index=False)
    logging.info(f'All translation or untranslation data ({lang}, count:{cnt}) are save to {save_file}')

def update_from_excel(save_file:str, proj: project_index, lang: str):
    use_cnt = 0
    unuse_cnt = 0
    df = pd.read_excel(save_file, sheet_name=None, na_filter=False)
    res = []
    for sheet in tqdm.tqdm(df.keys(), total=len(df), desc='Reading from the file...'):
        sheet_data = df[sheet]
        for tid, lang, new_str in zip(sheet_data[HEAD_NAME.INDEX_STR], sheet_data[HEAD_NAME.LANGUAGE_STR],
                                      sheet_data[HEAD_NAME.NEW_TEXT_STR]):
            tid, new_str = str(tid), str(new_str).strip()
            if new_str == '':
                new_str = None
            raw_text = proj.translate(tid, lang)
            if new_str == raw_text or (raw_text is not None and raw_text.strip() == new_str):
                unuse_cnt += 1
                continue
            res.append((tid, new_str))
            use_cnt += 1
    logging.info(f'There are {use_cnt} updated line(s) and {unuse_cnt} unused line(s) in {save_file}')
    return res


if __name__ == '__main__':
    import log.logger

    print(my_hash('sdsadasda'))
    print(my_hash('sdsadasda'))
    print(my_hash('sda'))
    print(my_hash('2'))
    print(my_hash('2阿斯顿'))
    print('======================================================================')
    p = project_index.init_from_dir(r'translated/tmp_renpy_game/game', 'test', 'V0.0.1', is_translated=False)
    my_lang = 'chinese'
    for s,t in p._raw_data.untranslated_lines[my_lang].items():
        print(s,f'({t.old_str})','->' ,t.old_str, flush=True)
    print('======================================================================')
    save_path = os.path.join(default_config.project_path, 'html', f'{p.full_name}.html')
    # save_to_html(save_path, p.untranslated_lines(my_lang))
    # exit(0)
    print(f'untranslation_size:{p.untranslation_size(my_lang)}')
    res = load_from_html(save_path, p.untranslated_lines(my_lang))
    p.update(res, my_lang)
    print(f'untranslation_size:{p.untranslation_size(my_lang)}=========>')
    for s,t in p._raw_data.untranslated_lines[my_lang].items():
        print(s,f'({t.old_str})' ,'->' ,t.new_str, flush=True)
    print(f'translation_size:{p.translation_size(my_lang)}*********>')
    for s,t in p._raw_data.translated_lines[my_lang].items():
        print(s,f'({t.old_str})' ,'->' ,t.new_str, flush=True)

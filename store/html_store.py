import hashlib
import logging
import os
from typing import List, Tuple

from config.config import default_config
from store.index import project_index

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
            if raw_text == unmap[encrypted_tid]:
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

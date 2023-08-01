import hashlib
import logging
from typing import List

from store.index import project_index

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
    <table>
        <tbody>
            <tr>
                <th>Translation ID</th><th>Raw Text</th>
            </tr>
{filler}
        </tbody>
    </table>
</body>
</html>
'''
TR_TEMPLATE = '<tr><td>S#2#{id}#E3#</td><td>B4##{text}#D5#</td></tr>\n'
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


def save_to_html(file_name: str, sources: List[str]):
    tr_arr = []
    for s in sources:
        tr_arr.append(TR_TEMPLATE.format(id=text_id(s), text=s))
    save_html = HTML_TEMPLATE.format(filler=''.join(tr_arr))
    with open(file_name, 'w', encoding='utf-8', newline='\n') as f:
        f.write(save_html)
    logging.info(f'Save untranslated {len(sources)} translations to {file_name}')


def load_from_html(file_name: str, sources: List[str]):
    unmap = dict()
    with open(file_name, 'r', encoding='utf-8') as f:
        i = 0
        for l in f:
            i += 1
            l = l.strip()
            if l.startswith('<tr><td') and l.endswith('</td></tr>'):
                id = l[l.find('S#2#') + 4:l.rfind('#E3#')].strip().upper()
                new_str = l[l.find('B4##') + 4:l.rfind('#D5#')].strip()
                if id == '' or new_str == '':
                    logging.info(f'[Line {i}] Skipping corrupted translation: {l}')
                else:
                    unmap[id] = new_str
    logging.info(f'Found {len(unmap)} translations in {file_name}')
    t_sources = []
    targets = []
    use_cnt = 0
    unuse_cnt = 0
    for s in sources:
        tid = text_id(s)
        if tid in unmap:
            if s.strip()!=unmap[tid]:
                use_cnt+=1
                t_sources.append(s)
                targets.append('@@'+unmap[tid])
            else:
                logging.warning(f'Untranslated text (Translation ID:{tid}, "{s}") found, it will be ignored!')
                unuse_cnt+=1
    logging.info(f'There are {use_cnt} translated line(s) and {unuse_cnt} untranslated line(s) in {file_name}')
    return (t_sources, targets)


if __name__ == '__main__':
    import log.logger

    print(my_hash('sdsadasda'))
    print(my_hash('sdsadasda'))
    print(my_hash('sda'))
    print(my_hash('2'))
    print(my_hash('2阿斯顿'))

    p = project_index.init_from_dir(r'translated/tmp_renpy_game/game', 'test', 'V0.0.1', is_translated=False)
    save_to_html(r'./a.html', p.untranslated_lines)
    print(f'untranslation_size:{p.untranslation_size}')
    s, t = load_from_html(r'D:\Users\Surface Book2\Downloads\公文.html', p.untranslated_lines)
    p.update(s, t)
    print(f'untranslation_size:{p.untranslation_size}')
    for s,t in p._raw_data.translated_lines.items():
        print(s,'->' ,t.new_str)

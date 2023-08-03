import logging

from tqdm import tqdm

from store.item import translation_item
from util.misc import text_type, TEXT_TYPE, is_empty


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
            if raw_text is None or i-raw_line != 1:
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
    logging.info(f'{rpy_file}: {save_cnt} untranslated line(s) are added. Other {unsave_cnt} untranslated line(s) are skipped!')

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
            if raw_text is None or i-raw_line != 1:
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
                logging.warning(f'{rpy_file}[L{i}]: The new text({text}) is not the same as the old text({raw_text})! It will be ignored for translation.')
                unsave_cnt += 1
            raw_text = None
            raw_line = -1
    logging.info(f'{rpy_file}: {save_cnt} untranslated line(s) are added. Other {unsave_cnt} untranslated line(s) are skipped!')
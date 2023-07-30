import logging

from tqdm import tqdm

from store.item import translation_item
from util.misc import text_type, TEXT_TYPE, is_empty


def update_translated_lines(rpy_file, translated_lines):
    with open(rpy_file, 'r', encoding='utf-8') as f:
        temp_data = f.readlines()
    raw_text = None
    for i, line in enumerate(temp_data, 1):
        text, ttype = text_type(line)
        if ttype == TEXT_TYPE.RAW:
            if is_empty(text):
                logging.warning(f'{rpy_file}[L{i}]: The old text({text}) is empty')
            raw_text = text
        if ttype == TEXT_TYPE.NEW:
            if raw_text is None:
                logging.error(f'{rpy_file}[L{i}]: Unmatched new text({text}), it will be skipped!')
                continue
            if is_empty(text):
                logging.warning(f'{rpy_file}[L{i}]: The new text({text}) is empty!')
            if raw_text in translated_lines:
                tline = translated_lines[raw_text]
                logging.warning(
                    f'{rpy_file}[L{i}]: The old translation({tline.new_str}) for "{raw_text}" will replace by “{text}”. This may result in error in renpy.')
                tline.new_str = text
            else:
                translated_lines[raw_text] = translation_item(
                    old_str=raw_text,
                    new_str=text,
                    file=rpy_file,
                    line=i
                )
            raw_text = None

def update_untranslated_lines(rpy_file, untranslated_lines):
    with open(rpy_file, 'r', encoding='utf-8') as f:
        temp_data = f.readlines()
    raw_text = None
    for i, line in enumerate(temp_data, 1):
        text, ttype = text_type(line)
        if ttype == TEXT_TYPE.RAW:
            if is_empty(text):
                logging.warning(f'{rpy_file}[L{i}]: The old text({text}) is empty.')
            raw_text = text
        if ttype == TEXT_TYPE.NEW:
            if raw_text is None:
                logging.info(f'{rpy_file}[L{i}]: Unmatched new text({text}). It is ok, noting that the new text and the old new text must be in pair while getting translated texts.')
                untranslated_lines[text] = translation_item(
                    old_str=text,
                    new_str=None,
                    file=rpy_file,
                    line=i
                )
                continue
            if raw_text == text:
                if raw_text in untranslated_lines:
                    untline = untranslated_lines[raw_text]
                    logging.warning(
                        f'{rpy_file}[L{i}]: The duplicate untranslated text({untline.new_str}) is found! This may result in error in renpy.')
                    untline.new_str = text
                untranslated_lines[raw_text] = translation_item(
                    old_str=raw_text,
                    new_str=None,
                    file=rpy_file,
                    line=i
                )
            else:
                logging.warning(f'{rpy_file}[L{i}]: The new text({text}) is not the same as the old text({raw_text})! It will be ignored for translation.')
            raw_text = None
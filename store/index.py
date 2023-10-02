import logging
import os.path
from collections import defaultdict
from functools import cmp_to_key
from typing import List, Tuple
import pickle

import pandas as pd
import tqdm
from pandas import ExcelWriter

from config.config import default_config
from store.fetch import update_translated_lines_new, update_untranslated_lines_new, preparse_rpy_file
from store.item import project_item_new, i18n_translation_dict, translation_item
from util.file import walk_and_select, mkdir, file_dir, exists_file
from util.misc import replacer, text_type, TEXT_TYPE


class project_index:
    def __init__(self, raw_data: project_item_new):
        self._raw_data = raw_data

    def untranslation_size(self, lang:str=None):
        self.check_lang(lang, False)
        return self._raw_data.untranslated_lines.len(lang)

    def translation_size(self, lang:str=None):
        self.check_lang(lang, True)
        return self._raw_data.translated_lines.len(lang)

    @property
    def source_dir(self):
        return self._raw_data.source_dir

    @property
    def num_rpys(self):
        return len(self._raw_data.rpy_files)

    @property
    def rpys(self):
        return self._raw_data.rpy_files.copy()

    @staticmethod
    def rpy_statistics(ryp_file):
        trans_dict, untrans_dict, invalid_dict = defaultdict(list), defaultdict(list), defaultdict(list)
        assert exists_file(ryp_file), 'File not found: {ryp_file}'
        new_i18n_dict, invalid_list = preparse_rpy_file(ryp_file, verbose=False)
        for lang, new_dict in new_i18n_dict.items():
            for tid, item in new_dict.items():
                if item.old_str != item.new_str:
                    trans_dict[lang].append(item)
                else:
                    untrans_dict[lang].append(item)
        for d in invalid_list:
            invalid_dict[d.lang].append(d)
        return trans_dict, untrans_dict, invalid_dict

    def untranslated_lines(self, lang:str):
        self.check_lang(lang, False)
        tid_texts = []
        for tid, item in self._raw_data.untranslated_lines[lang].items():
            tid_texts.append((tid, item.old_str))
        return tid_texts

    def translated_lines(self, lang:str):
        self.check_lang(lang, True)
        tid_texts = []
        for tid, item in self._raw_data.translated_lines[lang].items():
            tid_texts.append((tid, item.new_str))
        return tid_texts

    @property
    def untranslated_langs(self):
        return list(self._raw_data.untranslated_lines.langs())

    @property
    def translated_langs(self):
        return list(self._raw_data.translated_lines.langs())

    @property
    def full_name(self):
        return f'{self.project_name}_{self.project_tag}'

    @property
    def first_untranslated_lang(self):
        langs = self.untranslated_langs
        if len(langs) == 0: return None
        return langs[0]

    @property
    def first_translated_lang(self):
        langs = self.translated_langs
        if len(langs) == 0: return None
        return langs[0]

    @property
    def project_name(self):
        return self._raw_data.name

    @property
    def project_tag(self):
        return self._raw_data.tag

    @property
    def file_name(self):
        return f'{self.full_name}.pt'

    def update(self, tids_and_translated_texts: List[Tuple[str, str]], lang:str, skip_untrans_while_notin=True):
        self.check_lang(lang, False)
        self._raw_data.translated_lines.safe_add_key(lang)
        translated_lines = self._raw_data.translated_lines[lang]
        untranslated_lines = self._raw_data.untranslated_lines[lang]
        for tid, text in tids_and_translated_texts:
            checked = False
            if tid not in untranslated_lines:
                if skip_untrans_while_notin:
                    logging.warning(
                        f'Non-existent untranslated text (identifier={tid}) in untranslated_lines, this translation won\'t be added')
                    continue
            else:
                checked=True
            if tid in translated_lines:
                logging.warning(
                    f'Existent translated text for ({translated_lines[tid].old_str}) in translated_lines:{translated_lines[tid]}, \nit will be replaced by the new translation: {text}')
                tline = translated_lines[tid]
                tline.new_str = text
                if tid in untranslated_lines: untranslated_lines.pop(tid)
            elif checked:
                utline = untranslated_lines.pop(tid)
                utline.new_str = text
                translated_lines[tid] = utline
            else:
                logging.warning(
                    f'Discard the translated text ({text}) with unknown identifier: {tid}')

    def translate(self, tid:str, lang:str):
        if (lang, tid) in self._raw_data.translated_lines:
            return self._raw_data.translated_lines[(lang, tid)].new_str
        return None

    def untranslate(self, tid:str, lang:str):
        if (lang, tid) in self._raw_data.translated_lines:
            return self._raw_data.translated_lines[(lang, tid)].old_str
        if (lang, tid) in self._raw_data.untranslated_lines:
            return self._raw_data.untranslated_lines[(lang, tid)].old_str
        return None

    @classmethod
    def init_from_dir(cls, source_dir: str, name: str, tag: str, is_translated=True, strict=False):
        ryp_files = walk_and_select(source_dir, lambda x: x.endswith('.rpy'))
        lines = i18n_translation_dict()
        for rpy_file in tqdm.tqdm(ryp_files,
                                  desc=f'Getting {"translated" if is_translated else "untranslated"} texts from {source_dir}'):
            if is_translated:
                update_translated_lines_new(rpy_file, lines, strict=strict)
            else:
                update_untranslated_lines_new(rpy_file, lines, strict=strict)
        translated_lines = None
        untranslated_lines = None
        if is_translated:
            translated_lines = lines
            logging.info(f'{lines.len()} translated line(s) are stored.')
        else:
            untranslated_lines = lines
            logging.info(f'{lines.len()} untranslated line(s) are found.')
        raw_data = project_item_new(source_dir, name, tag, ryp_files,
                                translated_lines=translated_lines,
                                untranslated_lines=untranslated_lines)
        return cls(raw_data)

    def accept_untranslation(self, selected_lang:str=None):
        acce_cnt = 0
        selected_lang = self.select_or_check_lang(selected_lang, False)
        for lang, new_dict in self._raw_data.untranslated_lines.items():
            if selected_lang is not None and lang != selected_lang:
                continue
            for tid in list(new_dict.keys()):
                acce_cnt+=1
                new_line = new_dict.pop(tid)
                new_line.new_str = new_line.old_str
                if (lang, tid) in self._raw_data.translated_lines:
                    old_line = self._raw_data.translated_lines[(lang, tid)]
                    logging.warning(
                        f'{new_line.file}[L{new_line.line}]: Existent translation for ({new_line.old_str}) in translated_lines:{old_line}, it will be replaced by the new translation:{new_line.new_str}')
                self._raw_data.translated_lines[(lang, tid)] = new_line
        logging.info(
            f'{acce_cnt} untranslated line(s) are used as translated one(s)')

    def merge_from(self, proj, selected_lang:str=None):
        merge_cnt = 0
        unmerge_cnt = 0
        selected_lang = self.select_or_check_lang(selected_lang, False)
        for lang, new_dict in self._raw_data.untranslated_lines.items():
            if selected_lang is not None and lang != selected_lang:
                continue
            for tid in list(new_dict.keys()):
                trans_txt = proj.translate(tid, lang)
                if trans_txt is None:
                    unmerge_cnt += 1
                else:
                    merge_cnt += 1
                    untline = new_dict.pop(tid)
                    untline.new_str = trans_txt
                    if (lang, tid) in self._raw_data.translated_lines:
                        logging.warning(
                            f'{untline.file}[L{untline.line}]: Existent translation for ({untline.old_str}) in translated_lines:{self._raw_data.translated_lines[(lang, tid)]}, it will be replaced by the new translation:{trans_txt}')
                    self._raw_data.translated_lines[(lang, tid)] = untline
        logging.info(
            f'{merge_cnt} translated line(s) are used during merging, and there has {unmerge_cnt} untranslated line(s)')

    def perparse_with_linenumber(self, rpy_file, selected_lang:str=None, skip_unmatch=False, strict=False):
        new_i18n_dict = preparse_rpy_file(rpy_file, strict=strict)[0]
        linenumber_map = dict()
        for lang, new_dict in new_i18n_dict.items():
            if selected_lang is not None and lang != selected_lang:
                continue
            for tid, item in new_dict.items():
                line_no = item.line
                if skip_unmatch and item.old_str != item.new_str:
                    logging.warning(f'{item.file}[L{item.line}]: The item is skipped for old_str({item.old_str})!=new_str({item.new_str}):  \n\t{item}')
                    continue
                assert line_no not in linenumber_map, f'Duplicate translation line number:{line_no}.\n' \
                                                                f'\tDetailed info:\n' \
                                                                f'\told:{linenumber_map[line_no]}\n' \
                                                                f'\tnew:{item}'
                linenumber_map[line_no] = item
        return linenumber_map

    def check_lang(self, lang:str, is_translated_langs:bool):
        assert lang in (self.translated_langs if is_translated_langs else self.untranslated_langs),\
            f'The selected lang {lang} is not found! Available language(s) are {self.translated_langs if is_translated_langs else self.untranslated_langs}.'

    def select_or_check_lang(self, lang:str, is_translated_langs:bool, assert_existing=True):
        if lang is None:
            lang = self.first_translated_lang if is_translated_langs else self.first_untranslated_lang
            if assert_existing:
                assert lang is not None, f'Available {"translated" if is_translated_langs else "untranslated"} language(s) not Found!'
            logging.info(
                f'Selecting the default language {lang} for the current operation. If you want change to another language, please specify the argument {{lang}}.')
        else:
            self.check_lang(lang, is_translated_langs)
        return lang

    def apply_by_default(self, lang:str=None, strict=False):
        lang = self.select_or_check_lang(lang, True)
        self.apply(default_config.project_path, lang, strict=strict)

    def apply(self, save_dir:str, lang:str=None, strict=False):
        lang = self.select_or_check_lang(lang, True)
        save_dir = os.path.join(save_dir, self.full_name)
        mkdir(save_dir)
        rpy_files = walk_and_select(self.source_dir, lambda x: x.endswith('.rpy'))
        if lang in self.untranslated_langs and self.untranslation_size(lang) > 0:
            logging.warning(f'There still exists untranslated texts (qty:{self.untranslation_size(lang)}) in language {lang}.')
        apply_cnt = 0
        unapply_cnt = 0
        abs_source_dir = os.path.abspath(self.source_dir)
        for rpy_file in tqdm.tqdm(rpy_files,
                                  desc=f'Applying translated texts to {self.full_name} in language {lang}, you can found it in {save_dir}.'):
            rpy_file = os.path.abspath(rpy_file)
            preparsed_data = self.perparse_with_linenumber(rpy_file, selected_lang=lang, skip_unmatch=True, strict=strict)
            base_dir = os.path.join(save_dir, file_dir(rpy_file[len(abs_source_dir):]).strip(os.sep))
            mkdir(base_dir)
            r = replacer(rpy_file, save_dir=base_dir)
            r.start(force=True)
            apply_cnt_i = 0
            unapply_cnt_i = 0
            text = r.next()
            line_no = 1
            while text is not None:
                ori_text, ttype, _ = text_type(text)
                if ttype == TEXT_TYPE.NEW:
                    if line_no in preparsed_data:
                        parsed_item = preparsed_data[line_no]
                        trans_txt = self.translate(parsed_item.identifier, lang)
                        if trans_txt is None:
                            unapply_cnt_i += 1
                        else:
                            apply_cnt_i += 1
                            lb = text.find('"')
                            rb = text.rfind('"')
                            text = text[:lb+1] + trans_txt + text[rb:]
                    else:
                        unapply_cnt_i += 1
                r.update(text)
                text = r.next()
                line_no += 1
            logging.info(
                f'{rpy_file} is translated with {apply_cnt_i} translated line(s) and {unapply_cnt_i} untranslated line(s) in language {lang}.')
            apply_cnt += apply_cnt_i
            unapply_cnt += unapply_cnt_i
        logging.info(
            f'{len(rpy_files)} rpy file(s) are translated with {apply_cnt} translated line(s) and {unapply_cnt} untranslated line(s) in language {lang}.')
        logging.info(f'You can find output rpy files in {save_dir}.')


    def revert_by_default(self, lang:str=None, strict=False):
        lang = self.select_or_check_lang(lang, True)
        self.revert(default_config.project_path, lang, strict=strict)
    def revert(self, save_dir:str, lang:str=None, strict=False):
        lang = self.select_or_check_lang(lang, True)
        save_dir = os.path.join(save_dir, self.full_name)
        mkdir(save_dir)
        rpy_files = walk_and_select(self.source_dir, lambda x: x.endswith('.rpy'))
        apply_cnt = 0
        unapply_cnt = 0
        abs_source_dir = os.path.abspath(self.source_dir)
        for rpy_file in tqdm.tqdm(rpy_files,
                                  desc=f'Reverting translated texts on {self.full_name} in language {lang}, you can found it in {save_dir}.'):
            rpy_file = os.path.abspath(rpy_file)
            preparsed_data = self.perparse_with_linenumber(rpy_file, selected_lang=lang, skip_unmatch=False, strict=strict)
            base_dir = os.path.join(save_dir, file_dir(rpy_file[len(abs_source_dir):]).strip(os.sep))
            mkdir(base_dir)
            r = replacer(rpy_file, save_dir=base_dir)
            r.start(force=True)
            apply_cnt_i = 0
            unapply_cnt_i = 0
            text = r.next()
            line_no = 1
            while text is not None:
                ori_text, ttype, _ = text_type(text)
                if ttype == TEXT_TYPE.NEW:
                    raw_text = None
                    if line_no in preparsed_data:
                        parsed_item = preparsed_data[line_no]
                        raw_text = parsed_item.old_str
                        if raw_text is None:
                            raw_text = self.untranslate(parsed_item.identifier, lang)
                    if raw_text is None:
                        unapply_cnt_i += 1
                    else:
                        apply_cnt_i += 1
                        lb = text.find('"')
                        rb = text.rfind('"')
                        text = text[:lb+1] + raw_text + text[rb:]
                r.update(text)
                text = r.next()
                line_no += 1
            logging.info(
                f'{rpy_file} is untranslated with {apply_cnt_i} line(s) and {unapply_cnt_i} ignored line(s) in language {lang}.')
            apply_cnt += apply_cnt_i
            unapply_cnt += unapply_cnt_i
        logging.info(
            f'{len(rpy_files)} rpy file(s) are untranslated with {apply_cnt} line(s) and {unapply_cnt} ignored line(s) in language {lang}.')
        logging.info(f'You can find output rpy files in {save_dir}.')

    @classmethod
    def load_from_file(cls, file: str):
        with open(file, 'rb') as f:
            raw_data = pickle.load(f)
            return cls(raw_data)

    def save_by_default(self):
        self.save(os.path.join(default_config.project_path, self.file_name))

    def save(self, file: str):
        with open(file, 'wb') as f:
            pickle.dump(self._raw_data, f)

    def raw_untranslated_items(self, lang:str):
        self.check_lang(lang, False)
        return list(self._raw_data.untranslated_lines[lang].values())

    def raw_translated_items(self, lang:str):
        self.check_lang(lang, True)
        return list(self._raw_data.translated_lines[lang].values())


if __name__ == '__main__':
    import log.logger
    # p = project_index.init_from_dir(r'D:\projz\translated\tmp', 'test', 'V0.0.1', is_translated=False)
    # p.save(os.path.join(default_config.project_path, f'{p.full_name}.pt'))
    # p.apply(r'./proz')
    new_p =project_index.load_from_file(os.path.join(default_config.project_path, f'test_test.pt'))
    sources = ['']
    targets = []
    print(new_p._raw_data.untranslated_lines)
    # new_p.apply(r'./proz')

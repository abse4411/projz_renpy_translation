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
        assert lang in self.untranslated_langs, f'The selected_lang {lang} is not not Found! Available language(s) are {self.untranslated_langs}.'
        return self._raw_data.untranslated_lines.len(lang)

    def translation_size(self, lang:str=None):
        assert lang in self.translated_langs, f'The selected_lang {lang} is not not Found! Available language(s) are {self.translated_langs}.'
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
        assert lang in self.untranslated_langs, f'The selected_lang {lang} is not not Found! Available language(s) are {self.untranslated_langs}.'
        tid_texts = []
        for tid, item in self._raw_data.untranslated_lines[lang].items():
            tid_texts.append((tid, item.old_str))
        return tid_texts

    def translated_lines(self, lang:str):
        assert lang in self.translated_langs, f'The selected_lang {lang} is not not Found! Available language(s) are {self.translated_langs}.'
        tid_texts = []
        for tid, item in self._raw_data.translated_lines[lang].items():
            tid_texts.append((tid, item.old_str))
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

    def update(self, tids_and_translated_texts: List[Tuple[str, str]], lang:str):
        assert lang in self.untranslated_langs, f'The selected_lang {lang} is not not Found! Available language(s) are {self.untranslated_langs}.'
        self._raw_data.translated_lines.safe_add_key(lang)
        translated_lines = self._raw_data.translated_lines[lang]
        untranslated_lines = self._raw_data.untranslated_lines[lang]
        for tid, text in tids_and_translated_texts:
            if tid not in untranslated_lines:
                logging.warning(
                    f'Non-existent untranslated text (identifier={tid}) in untranslated_lines, this translation won\'t be added')
                continue
            else:
                if tid in translated_lines:
                    logging.warning(
                        f'Existent translated text for ({translated_lines[tid].old_str}) in translated_lines:{translated_lines[tid]}, it will be replaced by the new translation: {text}')
                    tline = translated_lines[tid]
                    tline.new_str = text
                    if tid in untranslated_lines: untranslated_lines.pop(tid)
                else:
                    utline = untranslated_lines.pop(tid)
                    utline.new_str = text
                    translated_lines[tid] = utline

    def translate(self, tid:str, lang:str):
        if (lang, tid) in self._raw_data.translated_lines:
            return self._raw_data.translated_lines[(lang, tid)].new_str
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
        if selected_lang is not None:
            assert selected_lang in self.untranslated_langs, f'The selected_lang {selected_lang} is not not Found! Available language(s) are {self.untranslated_langs}.'
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
        if selected_lang is not None:
            assert selected_lang in self.untranslated_langs, f'The selected_lang {selected_lang} is not not Found! Available language(s) are {self.untranslated_langs}.'
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


    def apply_by_default(self, lang:str=None, strict=False):
        if lang is None:
            lang = self.first_translated_lang
            logging.info(
                f'Selecting the default language {lang} for apply_by_default. If you want change to another language, please specify the argument {{lang}}.')
        self.apply(default_config.project_path, lang, strict=strict)

    def apply(self, save_dir:str, lang:str, strict=False):
        assert lang in self.translated_langs, f'The selected_lang {lang} is not not Found! Available language(s) are {self.translated_langs}.'
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
                            unapply_cnt += 1
                        else:
                            apply_cnt_i += 1
                            lb = text.find('"')
                            rb = text.rfind('"')
                            text = text[:lb+1] + trans_txt + text[rb:]
                    else:
                        unapply_cnt += 1
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

    def dump_to_excel(self, file_name: str):
        columns = ['Translation Identifier', 'Language', 'Raw Text', 'New Text', 'File', 'Line', 'Code Info']

        def sort_and_unpack(tran_list: list):
            def _item_cmp(x: translation_item, y: translation_item):
                if x.file < y.file:
                    return 1
                elif x.file == y.file:
                    if x.line < y.line:
                        return 1
                    elif x.line == y.line:
                        return 0
                return -1

            tran_list.sort(key=cmp_to_key(_item_cmp))
            excel_id_data = []
            excel_la_data = []
            excel_rt_data = []
            excel_nt_data = []
            excel_fi_data = []
            excel_li_data = []
            excel_co_data = []
            for d in tran_list:
                excel_id_data.append(d.identifier)
                excel_la_data.append(d.lang)
                excel_rt_data.append(d.old_str)
                excel_nt_data.append(d.new_str)
                excel_fi_data.append(d.file)
                excel_li_data.append(d.line)
                excel_co_data.append(d.code)
            return excel_id_data, excel_la_data, excel_rt_data, excel_nt_data, excel_fi_data, excel_li_data, excel_co_data

        pd_dict = dict()
        for lang in self.translated_langs + self.untranslated_langs:
            if lang in self.translated_langs and self.translation_size(lang) > 0:
                res = sort_and_unpack(list(self._raw_data.translated_lines[lang].values()))
                df = pd.DataFrame({columns[i]: res[i] for i in range(len(columns))})
                df.reindex(columns=columns)
                pd_dict[f'Translated {lang}'] = df
            if lang in self.untranslated_langs and self.untranslation_size(lang) > 0:
                res = sort_and_unpack(list(self._raw_data.untranslated_lines[lang].values()))
                df = pd.DataFrame({columns[i]: res[i] for i in range(len(columns))})
                df.reindex(columns=columns)
                pd_dict[f'Untranslated {lang}'] = df

        with ExcelWriter(file_name) as writer:
            for sheet_name in sorted(pd_dict.keys()):
                pd_dict[sheet_name].to_excel(writer, sheet_name=sheet_name, index=False)
        logging.info(f'All translation and untranslation data are save to {file_name}')


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

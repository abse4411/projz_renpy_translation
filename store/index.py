import logging
import os.path
from typing import List
import pickle

import tqdm

from config.config import default_config
from store.fetch import update_translated_lines, update_untranslated_lines
from store.item import project_item
from util.file import walk_and_select, mkdir, file_dir, file_name
from util.misc import replacer, text_type, TEXT_TYPE


class project_index:
    def __init__(self, raw_data: project_item):
        self._raw_data = raw_data

    @property
    def untranslation_size(self):
        return len(self._raw_data.untranslated_lines)

    @property
    def translation_size(self):
        return len(self._raw_data.translated_lines)

    @property
    def source_dir(self):
        return self._raw_data.source_dir

    @property
    def num_rpys(self):
        return len(self._raw_data.rpy_files)

    @property
    def untranslated_lines(self):
        return list(self._raw_data.untranslated_lines.keys())

    @property
    def full_name(self):
        return f'{self.project_name}_{self.project_tag}'

    @property
    def project_name(self):
        return self._raw_data.name

    @property
    def project_tag(self):
        return self._raw_data.tag

    def update(self, sources: List[str], targets: List[str]):
        assert len(sources) == len(targets)
        for s, t in zip(sources, targets):
            if s in self._raw_data.translated_lines:
                logging.warning(
                    f'Existent translated text for ({s}) in translated_lines:{self._raw_data.translated_lines[s]}, it will be replaced by the new translation: {t}')
                tline = self._raw_data.translated_lines[s]
                tline.new_str = t
            else:
                if s not in self._raw_data.untranslated_lines:
                    logging.warning(
                        f'Non-existent untranslated text "{s}" in untranslated_lines, this translation won\'t be added')
                    continue
                utline = self._raw_data.untranslated_lines.pop(s)
                utline.new_str = t
                self._raw_data.translated_lines[s] = utline

    def translate(self, source:str):
        if source in self._raw_data.translated_lines:
            return self._raw_data.translated_lines[source].new_str
        return None

    @classmethod
    def init_from_dir(cls, source_dir: str, name: str, tag: str, is_translated=True):
        ryp_files = walk_and_select(source_dir, lambda x: x.endswith('.rpy'))
        lines = dict()
        for rpy_file in tqdm.tqdm(ryp_files,
                                  desc=f'Getting {"translated" if is_translated else "untranslated"} texts from {source_dir}'):
            if is_translated:
                update_translated_lines(rpy_file, lines)
            else:
                update_untranslated_lines(rpy_file, lines)
        translated_lines = None
        untranslated_lines = None
        if is_translated:
            translated_lines = lines
            logging.info(f'{len(lines)} translated line(s) are stored.')
        else:
            untranslated_lines = lines
            logging.info(f'{len(lines)} untranslated line(s) are found.')
        raw_data = project_item(source_dir, name, tag, ryp_files,
                                translated_lines=translated_lines,
                                untranslated_lines=untranslated_lines)
        return cls(raw_data)

    def merge_from(self, proj: project_name):
        merge_cnt = 0
        unmerge_cnt = 0
        for s in self.untranslated_lines:
            trans_txt = proj.translate(s)
            if trans_txt is None:
                unmerge_cnt += 1
            else:
                merge_cnt += 1
                untline = self._raw_data.untranslated_lines.pop(s)
                untline.new_str = trans_txt
                if s in self._raw_data.translated_lines:
                    logging.warning(
                        f'Existent translation for ({s}) in translated_lines:{self._raw_data.translated_lines[s]}, it will be replaced by the new translation:{trans_txt}')
                self._raw_data.translated_lines[s] = untline
        logging.info(f'{merge_cnt} translated line(s) are used during merging, and there has {unmerge_cnt} untranslated line(s)')

    def apply_by_default(self):
        self.apply(default_config.project_path)

    def apply(self, save_dir:str):
        save_dir = os.path.join(save_dir, self.full_name)
        mkdir(save_dir)
        rpy_files = walk_and_select(self.source_dir, lambda x: x.endswith('.rpy'))
        if self.untranslation_size > 0:
            logging.warning(f'There still exists untranslated texts (qty:{self.untranslation_size}).')
        apply_cnt = 0
        unapply_cnt = 0
        abs_source_dir = os.path.abspath(self.source_dir)
        for rpy_file in tqdm.tqdm(rpy_files,
                                  desc=f'Applying translated texts to {self.full_name}, you can found it in {save_dir}.'):
            rpy_file = os.path.abspath(rpy_file)
            base_dir = os.path.join(save_dir, file_dir(rpy_file[len(abs_source_dir):]).strip(os.sep))
            mkdir(base_dir)
            r = replacer(rpy_file, save_dir=base_dir)
            r.start(force=True)
            apply_cnt_i = 0
            unapply_cnt_i = 0
            text = r.next()
            while text is not None:
                ori_text, ttype = text_type(text)
                if ttype == TEXT_TYPE.NEW:
                    trans_txt = self.translate(ori_text)
                    if trans_txt is None:
                        unapply_cnt += 1
                    else:
                        apply_cnt_i += 1
                        text = text.replace(ori_text, trans_txt)
                r.update(text)
                text = r.next()
            logging.info(
                f'{rpy_file} is translated with {apply_cnt_i} translated line(s) and {unapply_cnt_i} untranslated line(s).')
            apply_cnt += apply_cnt_i
            unapply_cnt += unapply_cnt_i
        logging.info(
            f'{len(rpy_files)} rpy file(s) is/are translated with {apply_cnt} translated line(s) and {unapply_cnt} untranslated line(s).')

    @classmethod
    def load_from_file(cls, file: str):
        with open(file, 'rb') as f:
            raw_data = pickle.load(f)
            return cls(raw_data)

    def save_by_default(self):
        self.save(os.path.join(default_config.project_path, f'{self.full_name}.pt'))

    def save(self, file: str):
        with open(file, 'wb') as f:
            pickle.dump(self._raw_data, f)


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

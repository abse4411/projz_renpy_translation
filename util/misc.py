import re
import os.path as osp

import numpy as np

from .file import exists_file, file_name


class TEXT_TYPE:
    OTHER = "OTHER"
    RAW = "RAW"
    NEW = "NEW"


def text_type(text: str):
    if text:
        text = text.strip()
        if text:
            first_quote = text.find("\"")
            last_quote = text.rfind("\"")
            # raw text or new text not found, both text must be in quotes.
            if first_quote == -1 or first_quote == last_quote:
                return None, TEXT_TYPE.OTHER
            old_pos = text.find("old ")
            # new_pos = text.find("new")
            shape_pos = text.find("# ")
            quote_content = text[first_quote + 1:last_quote]
            if (old_pos != -1 and old_pos < first_quote) or (shape_pos != -1 and shape_pos < first_quote):
                return quote_content, TEXT_TYPE.RAW
            return quote_content, TEXT_TYPE.NEW
    return None, TEXT_TYPE.OTHER


# match the variable
regex_var = re.compile(r'(\[[A-Za-z_]+[A-Za-z1-9_]*\])')
# match the tag
regex_tag = re.compile(r'\{[^}]*\}')
# match any alpha
alpha_re = re.compile(r'[A-Za-z]', re.S)


def var_list(text: str):
    if text is not None:
        return regex_var.findall(text)
    return []


def strip_tags(text: str):
    if text is not None:
        return regex_tag.sub('', text)
    return text


def contain_alpha(text: str):
    if text:
        return alpha_re.search(text) is not None
    return False

def is_empty(text: str):
    if text:
        return text.strip() == ""
    return True

def strip_breaks(text: str):
    if text is not None:
        return text.strip().replace('\r\n', '').replace('\n', '')
    return text


class replacer:
    def __init__(self, target_file, save_dir):
        with open(target_file, 'r', encoding='utf-8') as f:
            self.data = f.readlines()
        assert exists_file(target_file)
        self.save_file = osp.join(save_dir, file_name(target_file))
        self.start_idx = 0
        if exists_file(self.save_file):
            with open(self.save_file, 'r', encoding='utf-8') as f:
                temp_data = f.readlines()
                self.start_idx = len(temp_data)

    def start(self, force=False):
        if force:
            self.start_idx = 0
            self.file_handle = open(self.save_file, 'w', encoding='utf-8', newline='')
        else:
            if self.start_idx < len(self.data):
                self.file_handle = open(self.save_file, 'a', encoding='utf-8', newline='')
        return self.start_idx < len(self.data)

    def cur_line(self):
        return self.start_idx + 1

    def __len__(self):
        return len(self.data)

    def next(self):
        if self.start_idx < len(self.data):
            return self.data[self.start_idx]
        else:
            if hasattr(self, "file_handle"):
                self.file_handle.close()
        return None

    def update(self, text):
        if self.start_idx < len(self.data):
            self.file_handle.write(text)
            self.start_idx += 1
            if np.random.rand() > 0.99:
                self.file_handle.flush()

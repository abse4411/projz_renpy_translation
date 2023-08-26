import json
from collections import defaultdict
from typing import List, Dict, Union, Optional, Tuple


class translation_item:
    def __init__(self, old_str: str, new_str: Optional[str], file: str, line: int, lang: str = None, code: str = None,
                 identifier: str = None):
        self.old_str = old_str
        self.new_str = new_str
        self.file = file
        self.line = line
        self.lang = lang
        self.code = code
        self.identifier = identifier

    def __repr__(self):
        return json.dumps({
            'old_str': self.old_str,
            'new_str': self.new_str,
            'file': self.file,
            'line': self.line,
            'code': self.code,
            'language': self.lang,
            'identifier': self.identifier,
        }, ensure_ascii=False)


class i18n_translation_dict:
    def __init__(self):
        self.lang_dict = defaultdict(dict)

    def __getitem__(self, key: Union[str, List, Tuple]):
        if isinstance(key, str):
            lang = key
            if lang in self.lang_dict:
                return self.lang_dict[lang]
            return None
        elif isinstance(key, (tuple, list)) and len(key) == 2:
            lang, tid = key
            if lang in self.lang_dict:
                lang_data = self.lang_dict[lang]
                if tid in lang_data:
                    return lang_data[tid]
            return None
        else:
            raise RuntimeError('key should a string, or a list|type with size=2')

    def safe_add_key(self, key:str, value:dict=None):
        assert isinstance(key, str), 'key should a str'
        if value is not None:
            assert isinstance(key, dict), 'value should a dict or None'
        else:
            value = dict()
        if key not in self.lang_dict:
            self.lang_dict[key] = value

    def __setitem__(self, key: Union[List, Tuple], value):
        assert isinstance(key, (tuple, list)) and len(key) == 2, 'key should a list|type with size=2'
        lang, tid = key
        self.lang_dict[lang][tid] = value

    def __contains__(self, key: Union[str, List, Tuple]):
        if isinstance(key, str):
            lang = key
            return lang in self.lang_dict
        elif isinstance(key, (tuple, list)) and len(key) == 2:
            lang, tid = key
            if lang in self.lang_dict:
                lang_data = self.lang_dict[lang]
                return tid in lang_data
        else:
            raise RuntimeError('key should a string, or a list|type with size=2')
        return False

    def len(self, key: str = None):
        if isinstance(key, str):
            lang = key
            return len(self.lang_dict[lang])
        else:
            return sum([len(d) for d in self.lang_dict.values()])

    def langs(self):
        return self.lang_dict.keys()

    def items(self):
        return self.lang_dict.items()


class project_item_new:
    def __init__(self,
                 source_dir: str,
                 name: str,
                 tag: str,
                 rpy_files: List[str],
                 translated_lines: i18n_translation_dict = None,
                 untranslated_lines: i18n_translation_dict = None):
        self.source_dir = source_dir
        self.name = name
        self.tag = tag
        self.rpy_files = rpy_files
        self.translated_lines = translated_lines if translated_lines is not None else i18n_translation_dict()
        self.untranslated_lines = untranslated_lines if untranslated_lines is not None else i18n_translation_dict()

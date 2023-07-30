import json
from typing import List, Dict, Union, Optional


class translation_item:
    def __init__(self, old_str: str, new_str: Optional[str], file: str, line: int):
        self.old_str = old_str
        self.new_str = new_str
        self.file = file
        self.line = line

    def __repr__(self):
        return json.dumps({
            'old_str': self.old_str,
            'new_str': self.new_str,
            'file': self.file,
            'line': self.line,
        }, ensure_ascii=False)


class project_item:
    def __init__(self,
                 source_dir: str,
                 name: str,
                 tag: str,
                 rpy_files: List[str],
                 translated_lines: Dict[str, translation_item] = None,
                 untranslated_lines: Dict[str, translation_item] = None):
        self.source_dir = source_dir
        self.name = name
        self.tag = tag
        self.rpy_files = rpy_files
        self.translated_lines = translated_lines if translated_lines is not None else dict()
        self.untranslated_lines = untranslated_lines if untranslated_lines is not None else dict()

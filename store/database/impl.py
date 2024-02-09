# projz_renpy_translation, a translator for RenPy games
# Copyright (C) 2023  github.com/abse4411
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os
from typing import List

from tinydb import where, Query

from config import default_config
from store.database import BaseDao


def return_first(arr):
    return arr[0] if arr else None


class TranslationIndexDao(BaseDao):
    def __init__(self):
        super().__init__(os.path.join(default_config.project_path, 'index.db'))
        # self.db = TinyDB('db.json')

    def list(self):
        res = self.db.all()
        return [(i.doc_id, i) for i in res]

    def select_first(self, doc_id: int, nickname: str, tag: str = None):
        res = None
        if doc_id is not None:
            res = self.db.get(doc_id=doc_id)
        if res is None and nickname is not None:
            if tag is None:
                return self.db.get((where('nickname') == nickname))
            return self.db.get((where('nickname') == nickname) & (where('tag') == tag))
        return res

    def contains(self, data: dict, exclude_docid: int = None):
        if exclude_docid is None:
            return self.db.contains(Query().fragment(data))
        else:
            res = self.db.get(Query().fragment(data))
            if res is not None:
                return res.doc_id != exclude_docid
            return False

    def add(self, indexe_dict: dict):
        return self.db.insert(indexe_dict)

    def update(self, data: dict, doc_id: int):
        return self.db.update(data, doc_ids=[doc_id])

    def delete(self, doc_id: int):
        return self.db.remove(doc_ids=[doc_id])

    def delete_all(self):
        self.db.truncate()

    @classmethod
    def open(cls):
        return cls()


class TranslationDao(BaseDao):
    def __init__(self, db_file: str):
        super().__init__(db_file)
        # self.db = TinyDB('db.json')

    def add_batch(self, table_name: str, batch_data: List[dict]):
        return self.db.table(table_name).insert_multiple(batch_data)

    def delete_by_lang(self, table_name: str):
        return self.db.drop_table(table_name)

    def update_block(self, table_name: str, doc_id: int, blocks: List[dict]):
        return self.db.table(table_name).update({'block': blocks}, doc_ids=[doc_id])

    def update_blocks(self, table_name: str, doc_ids: List[int], blocks: List[List[dict]]):
        update_cols = []
        for block, doc_id in zip(blocks, doc_ids):
            update_cols.append([{'block': block}, doc_id])
        return self.db.table(table_name).update_multiple_by_id(update_cols)

    def list_langs(self):
        return self.db.tables()

    def list_by_lang(self, table_name: str):
        if table_name in self.list_langs():
            return self.db.table(table_name).all()
        return []

    def select_first_by_docid(self, table_name: str, doc_id: int):
        if table_name in self.list_langs():
            return self.db.table(table_name).get(doc_id=doc_id)
        return None

    def select_first_by_identifier(self, table_name: str, identifier: str):
        if table_name in self.list_langs():
            return self.db.table(table_name).get(where('identifier') == identifier)
        return None

    def contains_with_docid(self, table_name: str, doc_id: int):
        if table_name in self.list_langs():
            return self.db.table(table_name).contains(doc_id=doc_id)
        return False

    def contains_with_identifier(self, table_name: str, identifier: str):
        if table_name in self.list_langs():
            return self.db.table(table_name).contains(where('identifier') == identifier)
        return False

    @classmethod
    def open(cls, db_file: str):
        return cls(db_file)

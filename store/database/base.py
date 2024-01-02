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
import logging
import threading

from tinydb import TinyDB, JSONStorage
from tinydb.middlewares import CachingMiddleware

from config import default_config
from store.database.table import ProjzTable

_DB_POOL = dict()
_CONTEXT_CNT = 0
_CONTEXT_LOCK = threading.Lock()


def _enter_context():
    global _CONTEXT_CNT
    _CONTEXT_LOCK.acquire()

    logging.debug(f'Enter context: {_CONTEXT_CNT}->{_CONTEXT_CNT + 1}')
    _CONTEXT_CNT += 1

    _CONTEXT_LOCK.release()


def _clear_dbs():
    # close all db
    for k, v in _DB_POOL.items():
        try:
            logging.debug(f'Closing db: {k}, num_holders: {v[1]}')
            v[0].close()
        except Exception as e:
            logging.exception(e)
    _DB_POOL.clear()


def flush():
    """
    write all cached data of each db to disk immediately
    :return:
    """
    global _CONTEXT_CNT
    _CONTEXT_LOCK.acquire()

    logging.debug(f'Flush: {_CONTEXT_CNT}')
    for k, v in _DB_POOL.items():
        try:
            logging.debug(f'Flush db: {k}, num_holders: {v[1]}')
            v[0].flush()
        except Exception as e:
            logging.exception(e)

    _CONTEXT_LOCK.release()


def _exit_context():
    global _CONTEXT_CNT
    _CONTEXT_LOCK.acquire()

    logging.debug(f'Quit context: {_CONTEXT_CNT}->{_CONTEXT_CNT - 1}')
    _CONTEXT_CNT -= 1
    if _CONTEXT_CNT <= 0:
        _CONTEXT_CNT = 0
        _clear_dbs()

    _CONTEXT_LOCK.release()


def _get_or_create(db_file: str):
    global _CONTEXT_CNT
    _CONTEXT_LOCK.acquire()

    logging.debug(f'Enter context: {_CONTEXT_CNT}->{_CONTEXT_CNT + 1}')
    _CONTEXT_CNT += 1
    try:
        if db_file in _DB_POOL:
            db, cnt = _DB_POOL[db_file]
            logging.debug(f'Get db: {db_file}, num_holders: {cnt}->{cnt + 1}')
            cnt += 1
            _DB_POOL[db_file] = (db, cnt)
        else:
            logging.debug(f'Create db: {db_file}')
            db = TinyDB(db_file, encoding='utf-8', ensure_ascii=False, storage=CachingMiddleware(JSONStorage))
            _DB_POOL[db_file] = (db, 1)
        return db
    finally:
        _CONTEXT_LOCK.release()


def _release(db_file: str):
    global _CONTEXT_CNT
    _CONTEXT_LOCK.acquire()

    logging.debug(f'Quit context: {_CONTEXT_CNT}->{_CONTEXT_CNT - 1}')
    _CONTEXT_CNT -= 1
    try:
        if db_file in _DB_POOL:
            db, cnt = _DB_POOL[db_file]
            logging.debug(f'Release db: {db_file}, num_holders: {cnt}->{cnt - 1}')
            cnt -= 1
            _DB_POOL[db_file] = (db, cnt)
            # if cnt <= 0:
            #     _DB_POOL.pop(db_file)
            #     db.close()
    finally:
        if _CONTEXT_CNT <= 0:
            _CONTEXT_CNT = 0
            _clear_dbs()
        _CONTEXT_LOCK.release()


def db_context(func):
    def wrapper(*args, **kwargs):
        _enter_context()
        try:
            return func(*args, **kwargs)
        finally:
            _exit_context()

    return wrapper


# use our table impl. to support update_multiple_by_id
TinyDB.table_class = ProjzTable


class BaseDao:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.db = None
        cache_size = default_config.write_cache_size
        if cache_size < 10:
            logging.warning(f'Low write_cache_size({cache_size}) means more frequent disk I/O operations,'
                            f' it may cause a high system load.')
            cache_size = max(cache_size, 50)
        CachingMiddleware.WRITE_CACHE_SIZE = cache_size

    def __enter__(self):
        # Using a CachingMiddleware to improves speed by reducing disk I/O
        self.db = _get_or_create(self.db_file)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _release(self.db_file)
        return False

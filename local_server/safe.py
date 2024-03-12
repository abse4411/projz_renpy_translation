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
import threading
from queue import Queue
from typing import Any


class SafeDict(dict):
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()

    def get(self, __key):
        with self._lock:
            return super().get(__key)

    def pop(self, k, d=None):
        with self._lock:
            return super().pop(k, d)

    def update(self, __m, **kwargs):
        with self._lock:
            super().update(__m, **kwargs)

    def copy(self):
        with self._lock:
            return super().copy()

    def __contains__(self, item):
        with self._lock:
            return super().__contains__(item)

    def __getitem__(self, item):
        with self._lock:
            return super().__getitem__(item)

    def __setitem__(self, key, value):
        with self._lock:
            super().__setitem__(key, value)

    def __len__(self):
        with self._lock:
            return super().__len__()


class LockObject:
    def __init__(self, obj=None):
        self._obj = obj
        self._lock = threading.Lock()

    def get(self):
        with self._lock:
            return self._obj

    def set(self, obj):
        with self._lock:
            self._obj = obj

    def lock_get(self):
        if self._lock.locked():
            return self._obj
        else:
            return self.get()

    def lock_set(self, obj):
        if self._lock.locked():
            self._obj = obj
        else:
            return self.set(obj)

    def __enter__(self):
        self._lock.acquire()
        return self._obj

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()
        return False

# class QueryableQueue(Queue):
#
#     def __init__(self, maxsize=0):
#         super().__init__(maxsize)
#         self._lock = threading.Lock()
#         self._item_set = set()
#
#     def put(self, item, block=..., timeout=...):
#         with self._lock:
#             item_id, data = item
#             self._item_set.add(item_id)
#             super().put(item, block, timeout)
#
#     def get(self, block=..., timeout=...):
#         with self._lock:
#             item = super().get(block, timeout)
#             self._item_set.remove(item[0])
#             return item
#
#     def __contains__(self, item_id: Any):
#         with self._lock:
#             return item_id in self._item_set

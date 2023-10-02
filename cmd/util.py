import glob
import os
from typing import List

from config.config import default_config


def _list_projects():
    return sorted(glob.glob(os.path.join(default_config.project_path, '*.pt')))


def _list_projects_and_select(indexes: List[int]):
    projs = _list_projects()
    res = []
    for i in indexes:
        i = int(i)
        assert 0 <= i < len(projs), f'index {i} out of range, available indexes are:{list(range(len(projs)))}'
        res.append(projs[i])
    return res

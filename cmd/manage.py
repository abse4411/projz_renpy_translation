import logging
import os
from collections import defaultdict

import prettytable
from prettytable import PrettyTable

from cmd.util import _list_projects_and_select, _list_projects
from config.config import default_config
from store.index import project_index
from util.misc import yes


def delete_cmd(proj_idx: int):
    # projs = _list_projects()
    proj = _list_projects_and_select([proj_idx])[0]
    if yes(f'Are your sure to delete {proj}?'):
        os.remove(proj)
        logging.warning(f'{proj} is deleted!')


def clear_cmd():
    projs = _list_projects()
    if len(projs) <= 0:
        print(f'There are not projects in {default_config.project_path}')
    print(f'The following {len(projs)} project(s) will be cleared:')
    for p in projs:
        print(p)
    if yes(f'Are your sure to delete these {len(projs)} project(s)?'):
        for p in projs:
            os.remove(p)
            logging.warning(f'{p} is deleted!')


def list_cmd(proj_idx: int = None):
    if proj_idx is None:
        projs = _list_projects()
        print(f'there are {len(projs)} projects in {default_config.project_path}')
        projs = [project_index.load_from_file(p) for p in projs]
        table = PrettyTable(
            ['Project Index', 'Project', 'Tag', 'Translated line(s)', 'Untranslated line(s)', 'Source dir', 'Num Rpys'])
        table.hrules = prettytable.ALL
        for i, p in enumerate(projs):
            untrans_cnt = '\n'.join([f'{l}: {p.untranslation_size(l)}' for l in p.untranslated_langs])
            trans_cnt = '\n'.join([f'{l}: {p.translation_size(l)}' for l in p.translated_langs])
            table.add_row(
                [i, p.project_name, p.project_tag, trans_cnt, untrans_cnt, p.source_dir,
                 p.num_rpys])
        print(table)
    else:
        proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
        table = PrettyTable(
            ['Project', 'Tag', 'Translated line(s)', 'Untranslated line(s)', 'Source dir', 'Num Rpys'])
        untrans_cnt = '\n'.join([f'{l}: {proj.untranslation_size(l)}' for l in proj.untranslated_langs])
        trans_cnt = '\n'.join([f'{l}: {proj.translation_size(l)}' for l in proj.translated_langs])
        table.add_row(
            [proj.project_name, proj.project_tag, trans_cnt, untrans_cnt, proj.source_dir,
             proj.num_rpys])
        print(table)
        table = PrettyTable(
            ['Rpy file', 'Translated line(s)', 'Untranslated line(s)', 'Invalid line(s)', 'Sum'])
        table.hrules = prettytable.ALL

        def _get_statistics(lang_dict):
            cnt = 0
            lang_arr = []
            for k, v in lang_dict.items():
                lang_arr.append(f'{k}: {len(v)}')
                cnt += len(v)
            return lang_arr, cnt

        def _add(accum, lang_dict):
            for k, v in lang_dict.items():
                accum[k] += v

        tot_trans, tot_untran, tot_invalid = defaultdict(list), defaultdict(list), defaultdict(list)
        for f in proj.rpys:
            trans_dict, untrans_dict, invalid_dict = project_index.rpy_statistics(f)
            (t, tc), (ut, utc), (a, ac) = _get_statistics(trans_dict), _get_statistics(untrans_dict), _get_statistics(
                invalid_dict)
            _add(tot_trans, trans_dict)
            _add(tot_untran, untrans_dict)
            _add(tot_invalid, invalid_dict)
            table.add_row([f, '\n'.join(t), '\n'.join(ut), '\n'.join(a), tc + utc + ac])
        (t, tc), (ut, utc), (a, ac) = _get_statistics(tot_trans), _get_statistics(tot_untran), _get_statistics(
            tot_invalid)
        table.add_row(['Sum', '\n'.join(t), '\n'.join(ut), '\n'.join(a), tc + utc + ac])
        print(table)

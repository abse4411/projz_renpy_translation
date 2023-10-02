import distutils

from cmd.util import _list_projects_and_select
from store.index import project_index
from util.file import file_name
from util.misc import yes


def acceptuntrans_cmd(proj_idx: int, lang: str = None):
    # projs = _list_projects()
    project_name = _list_projects_and_select([proj_idx])[0]
    proj = project_index.load_from_file(project_name)
    if yes(f'Accept all untranslated texts as translated texts for project: {project_name}?'):
        proj.accept_untranslation(lang)
        proj.save_by_default()


def merge_cmd(source_idx: int, target_idx: int, lang: str = None):
    source_idx, target_idx = int(source_idx), int(target_idx)
    assert source_idx != target_idx, f'source_idx({source_idx}) should diff from target_idx({target_idx}).'
    sproj, tproj = _list_projects_and_select([source_idx, target_idx])
    if yes(f'Merge all translated texts from {file_name(sproj)} to {file_name(tproj)}?'):
        sproj = project_index.load_from_file(sproj)
        tproj = project_index.load_from_file(tproj)
        tproj.merge_from(sproj, lang)
        tproj.save_by_default()


def apply_cmd(proj_idx: int, lang: str = None, greedy: bool = True):
    # projs = _list_projects()
    strict_mode = not (distutils.util.strtobool(greedy) if isinstance(greedy, str) else greedy)
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    proj.apply_by_default(lang, strict=strict_mode)

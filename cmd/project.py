import distutils

from cmd.util import _list_projects_and_select
from store.index import project_index
from util.file import file_name
from util.misc import yes


def acceptuntrans_cmd(proj_idx: int, lang: str = None):
    # projs = _list_projects()
    project_name = _list_projects_and_select([proj_idx])[0]
    proj = project_index.load_from_file(project_name)
    lang = proj.select_or_check_lang(lang, False)
    if yes(f'Accept all untranslated texts ({lang}) as translated texts for project: {project_name}?'):
        proj.accept_untranslation(lang)
        proj.save_by_default()


def merge_cmd(source_idx: int, target_idx: int, lang: str = None):
    source_idx, target_idx = int(source_idx), int(target_idx)
    assert source_idx != target_idx, f'source_idx({source_idx}) should diff from target_idx({target_idx}).'
    sproj_file, tproj_file = _list_projects_and_select([source_idx, target_idx])
    sproj = project_index.load_from_file(sproj_file)
    tproj = project_index.load_from_file(tproj_file)
    lang = tproj.select_or_check_lang(lang, False)
    if yes(f'Merge all translated texts ({lang}) from {file_name(sproj_file)} to {file_name(tproj_file)}?'):
        tproj.merge_from(sproj, lang)
        tproj.save_by_default()


def apply_cmd(proj_idx: int, lang: str = None, greedy: bool = True):
    # projs = _list_projects()
    strict_mode = not (distutils.util.strtobool(greedy) if isinstance(greedy, str) else greedy)
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    proj.apply_by_default(lang, strict=strict_mode)

from cmd.util import _list_projects_and_select
from config.config import default_config
from store.index import project_index
import logging


def translate_cmd(proj_idx: int, api_name: str, num_workers: int = None, lang: str = None):
    # projs = _list_projects()
    if num_workers is not None:
        num_workers = int(num_workers)
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    lang = proj.select_or_check_lang(lang, False)
    assert api_name.strip() != '', f'API name is empty!'
    if proj.untranslation_size(lang) <= 0:
        logging.info(f'All texts in {proj.full_name} of language {lang} are translated!')
        return
    driver_path = default_config.get_global('CHROME_DRIVER')

    def save_import():
        try:
            import trans.web
            return trans.web
        except Exception as e:
            logging.exception(e)
        return None

    wt = save_import()
    if wt is not None:
        translator_class = wt.web_translator.__dict__[api_name]
        translator = wt.thread_trans.concurrent_translator(proj, lambda: translator_class(driver_path),
                                                           num_workers=num_workers)
        translator.start(lang)
        proj.save_by_default()
    else:
        print(
            'To use the web translator, please install the package "selenium" (pip install selenium) and download a compatible chrome driver for your chrome brower.\n'
            'You can find chrome drivers in this website: https://chromedriver.storage.googleapis.com/index.html (Version under 116) '
            'or https://googlechromelabs.github.io/chrome-for-testing/#stable (Version 116 or higher).\n'
            'Then config the path of chrome driver in config.ini (CHROME_DRIVER=Your path (chromedriver.exe))')


def dltranslate_cmd(proj_idx: int, model_name: str, lang: str = None):
    # projs = _list_projects()
    proj = project_index.load_from_file(_list_projects_and_select([proj_idx])[0])
    lang = proj.select_or_check_lang(lang, False)
    assert model_name.strip() != '', f'model name is empty!'
    if proj.untranslation_size(lang) <= 0:
        logging.info(f'All texts in {proj.full_name} of language {lang} are translated!')
        return

    def save_import():
        try:
            import trans.ai
            return trans.ai
        except Exception as e:
            logging.exception(e)
        return None

    wt = save_import()
    if wt is not None:
        assert model_name in wt.AVAILABLE_MODELS, f'model name must be one of {wt.AVAILABLE_MODELS}'
        t = wt.trans_wrapper(proj, model_name)
        t.translate_all(lang)
        proj.save_by_default()
    else:
        print(
            'To use the AI translator, please install these listed packages in requirement.txt. (pip install -r requirements.txt)\n'
            'You can also use the pytorch with CUDA support to enable faster translation, see: https://pytorch.org/\n')

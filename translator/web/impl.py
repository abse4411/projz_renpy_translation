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
import random
import time
from typing import Optional, List, Tuple

from config.base import ProjzConfig
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from translator.base import CachedTranslatorTemplate
from translator.web.base import register_translator
from util.translate import BatchTranslator


def _init_chrome(config: ProjzConfig):
    options = webdriver.ChromeOptions()
    options.add_argument("window-size=1920x1080")
    print("Starting chromedriver...")
    driver_path = config['translator']['web']['chrome_driver_path']
    try:
        s = Service(driver_path)
        browser = webdriver.Chrome(service=s, options=options)
    except SessionNotCreatedException as e:
        logging.exception(e)
        print(
            'Error in starting chromedriver, you may find the compatible chromedriver for your Chrome from '
            'https://registry.npmmirror.com/binary.html?path=chromedriver/ '
            'or https://googlechromelabs.github.io/chrome-for-testing/#stable')
        raise e
    return browser


class BaseChromeTranslator(CachedTranslatorTemplate):
    def __init__(self):
        super().__init__()
        self._browser = None
        self._batch_translator = None

    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)
        self._browser = _init_chrome(config)
        tconfig = config['translator']['web']
        _separator = tconfig['batch_separator']
        _max_len = tconfig['batch_max_textlen']
        _batch_size = tconfig['batch_size']
        self._batch_translator = BatchTranslator(self, _separator, _max_len, _batch_size, False)
        return True

    def close(self):
        try:
            if self._browser:
                self._browser.quit()
        except Exception as e:
            logging.exception(e)

    def set_input(self, rawtext):
        pass

    def get_output(self, rawtext) -> Optional[str]:
        pass

    def clear(self):
        pass

    def translate(self, rawtext) -> Optional[str]:
        self.set_input(rawtext)
        new_text = self.get_output(rawtext)
        self.clear()
        return new_text

    def translate_batch(self, texts: List[str]) -> List[str]:
        return self._batch_translator.translate_batch(texts)


class GoogleTranslator(BaseChromeTranslator):
    def __init__(self):
        super().__init__()
        self.inputArea = None

    def do_init(self, args, config: ProjzConfig):
        super().do_init(args, config)
        self._browser.get('https://translate.google.com/')
        print('Wait the browser for loading the page...')
        time.sleep(5)
        try:
            self._browser.find_element(By.XPATH,
                                       '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div/button').click()
        except:
            pass
        self.inputArea = self._browser.find_element(By.XPATH,
                                                    '/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[2]/div/c-wiz/span/span/div/textarea')
        return True

    def set_input(self, rawtext):
        self.inputArea.send_keys(rawtext)
        time.sleep(random.uniform(0.2, 1))

    def get_output(self, rawtext) -> Optional[str]:
        xpath = '/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[2]/c-wiz/div/div[6]/div/div[1]'
        WebDriverWait(self._browser, 10).until(
            lambda broswer: self._browser.find_element(By.XPATH, xpath))
        time.sleep(random.uniform(0.2, 1))
        text = self._browser.find_element(By.XPATH, xpath)
        res = text.text
        return res

    def clear(self):
        try:
            self._browser.find_element(By.XPATH,
                                       '/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[2]/div/c-wiz/div[1]/div/div[1]/span/button').click()
        except:
            pass
        try:
            self.inputArea.click()
            self.inputArea.send_keys(Keys.CONTROL, 'a')
            self.inputArea.send_keys(Keys.BACKSPACE)
        except:
            self.inputArea.clear()
        time.sleep(random.uniform(0.2, 1))


register_translator('google', GoogleTranslator)

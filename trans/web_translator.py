import logging
import random
import time
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from config.config import default_config
from trans.base import translator


def init_chrome(driver_path):
    options = webdriver.ChromeOptions()
    options.add_argument("window-size=1920x1080")
    logging.info("Starting chromedriver...")
    try:
        s = Service(driver_path)
        browser = webdriver.Chrome(service=s, options=options)
    except SessionNotCreatedException as err:
        logging.error(
            'Error in starting chromedriver, you may find the compatible chromedriver for your Chrome from https://registry.npmmirror.com/binary.html?path=chromedriver/')
        raise err
    return browser


class abstract_web_translator(translator):
    def __init__(self, driver_path):
        self.browser = init_chrome(driver_path)

    def close(self):
        try:
            self.browser.quit()
            self.browser.stop_client()
        except Exception as err:
            logging.error(err)

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

class caiyun(abstract_web_translator):
    def __init__(self, driver_path):
        super().__init__(driver_path)
        self.browser.get('https://fanyi.caiyunapp.com/')
        print('Wait the browser for loading the page...')
        time.sleep(5)
        self.inputArea = self.browser.find_element(By.CLASS_NAME, 'textinput')
        self.tran_button = self.browser.find_element(By.XPATH, '//*[@id="app"]/div[2]/div[1]/div[2]/div/div[1]/div[3]')

    def set_input(self, rawtext):
        self.inputArea.send_keys(rawtext)
        self.tran_button.click()
        time.sleep(random.uniform(0.2, 1))

    def get_output(self, rawtext) -> Optional[str]:
        try:
            xpath = '//*[@id="texttarget"]/div/span'
            WebDriverWait(self.browser, 10).until(
                lambda broswer: self.browser.find_element(By.XPATH, xpath))
            text = self.browser.find_element(By.XPATH, xpath)
            res = text.text
        except Exception as e:
            logging.error(f'Error in translating “{rawtext}”: {e}')
            return None
        return res

    def clear(self):
        try:
            self.browser.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[1]/div[2]/div/div[2]/div/div[1]/div').click()
            self.inputArea.click()
            self.inputArea.send_keys(Keys.CONTROL, 'a')
            self.inputArea.send_keys(Keys.BACKSPACE)
        except:
            self.inputArea.clear()
        time.sleep(random.uniform(0.2, 1))


class youdao(abstract_web_translator):
    def __init__(self, driver_path):
        super().__init__(driver_path)
        self.browser.get('https://fanyi.youdao.com/')
        print('Wait the browser for loading the page...')
        time.sleep(5)
        self.inputArea = self.browser.find_element(By.ID, 'js_fanyi_input')

    def set_input(self, rawtext):
        self.inputArea.send_keys(rawtext)
        time.sleep(random.uniform(0.2, 1))

    def get_output(self, rawtext) -> Optional[str]:
        try:
            xpath = '/html/body/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[3]/div[2]/div[1]'
            WebDriverWait(self.browser, 10).until(
                lambda broswer: self.browser.find_element(By.XPATH, xpath))
            time.sleep(random.uniform(0.2, 1))
            text = self.browser.find_element(By.XPATH, xpath)
            res = text.text
        except Exception as e:
            logging.error(f'Error in translating “{rawtext}”: {e}')
            return None
        return res

    def clear(self):
        try:
            self.browser.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[1]/a').click()
            self.inputArea.click()
            self.inputArea.send_keys(Keys.CONTROL, 'a')
            self.inputArea.send_keys(Keys.BACKSPACE)
        except:
            self.inputArea.clear()
        time.sleep(random.uniform(0.2, 1))

class baidu(abstract_web_translator):
    def __init__(self, driver_path):
        super().__init__(driver_path)
        self.browser.get('https://fanyi.baidu.com/')
        print('Wait the browser for loading the page...')
        time.sleep(5)
        try:
            self.browser.find_element(By.XPATH, '/html/body/div[1]/div[7]/div/div/div/a[2]').click()
        except:
            pass
        self.inputArea = self.browser.find_element(By.ID, 'baidu_translate_input')
        self.tran_button = self.browser.find_element(By.XPATH, '/html/body/div[1]/div[2]/div/div/div[1]/div[1]/div[1]/a[5]')

    def set_input(self, rawtext):
        self.inputArea.send_keys(rawtext)
        self.tran_button.click()
        time.sleep(random.uniform(0.2, 1))

    def get_output(self, rawtext) -> Optional[str]:
        try:
            xpath = '/html/body/div[1]/div[2]/div/div/div[1]/div[2]/div[1]/div[2]/div/div/div[1]/p[2]'
            WebDriverWait(self.browser, 10).until(
                lambda broswer: self.browser.find_element(By.XPATH, xpath))
            time.sleep(random.uniform(0.2, 1))
            all_texts = self.browser.find_elements(By.CLASS_NAME, 'target-output')
            text = []
            for t in all_texts:
                text.append(t.text)
            text = ''.join(text)
            res = text
        except Exception as e:
            logging.error(f'Error in translating “{rawtext}”: {e}')
            return None
        return res

    def clear(self):
        try:
            self.browser.find_element(By.XPATH, '/html/body/div[1]/div[2]/div/div/div[1]/div[2]/div[1]/div[1]/div/div[3]/a').click()
            self.inputArea.click()
            self.inputArea.send_keys(Keys.CONTROL, 'a')
            self.inputArea.send_keys(Keys.BACKSPACE)
        except:
            self.inputArea.clear()
        time.sleep(random.uniform(0.2, 1))

class google(abstract_web_translator):
    def __init__(self, driver_path):
        super().__init__(driver_path)
        self.browser.get('https://translate.google.com/')
        print('Wait the browser for loading the page...')
        time.sleep(5)
        try:
            self.browser.find_element(By.XPATH,
                                      '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div/button').click()
        except:
            pass
        self.inputArea = self.browser.find_element(By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[1]/span/span/div/textarea')

    def set_input(self, rawtext):
        self.inputArea.send_keys(rawtext)
        time.sleep(random.uniform(0.2, 1))

    def get_output(self, rawtext) -> Optional[str]:
        try:
            xpath = '/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div/div[2]/div[3]/c-wiz[2]/div/div[9]/div/div[1]'
            WebDriverWait(self.browser, 10).until(
                lambda broswer: self.browser.find_element(By.XPATH, xpath))
            time.sleep(random.uniform(0.2, 1))
            text = self.browser.find_element(By.XPATH, xpath)
            res = text.text
        except Exception as e:
            logging.error(f'Error in translating “{rawtext}”: {e}')
            return None
        return res

    def clear(self):
        try:
            self.browser.find_element(By.XPATH, '/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[1]/div[1]/div/div[1]/span/button').click()
            self.inputArea.click()
            self.inputArea.send_keys(Keys.CONTROL, 'a')
            self.inputArea.send_keys(Keys.BACKSPACE)
        except:
            self.inputArea.clear()
        time.sleep(random.uniform(0.2, 1))

if __name__ == '__main__':
    dp = default_config.get_global('CHROME_DRIVER')
    raw_texts = [
        'Hello wolrd!',
        'What a nice day!',
        'What time is it now?',
    ]
    raw_texts = raw_texts * 10

    t = youdao(dp)
    try:
        pass
        for text in raw_texts:
            res = t.translate(text)
            print(f'RAW:{text}, NEW:{res}')
        pass
    except Exception as e:
        print(e)
        t.close()
    finally:
        t.close()


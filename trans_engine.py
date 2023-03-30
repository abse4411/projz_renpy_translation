import random
import random
import re
import time

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from misc import strip_tags, strip_breaks


# Abstract translator
class translator:

    def translate(self, rawtext):
        return rawtext

class dict_translator(translator):
    def __init__(self, translated_text):
        self.translated_text = translated_text

    def translate(self, rawtext):
        if rawtext in self.translated_text:
            return self.translated_text[rawtext]
        return rawtext

class google(translator):
    def __init__(self, browser):
        self.browser = browser
        browser.get('https://translate.google.com/')
        print('等待网页加载...')
        time.sleep(5)
        self.inputArea = browser.find_element(By.XPATH,
                                              '//*[@id="yDmH0d"]/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[1]/span/span/div/textarea')
        try:
            # 切换到英语
            browser.find_element(By.XPATH, '/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[1]/c-wiz/div[1]/c-wiz/div[2]/div/div[2]/div/div/span/button[2]').click()
            time.sleep(1)
        except:
            pass


    def translate(self, rawtext):
        rawtext = strip_breaks(rawtext)
        res = rawtext
        self.inputArea.send_keys(rawtext)
        xpath = '//*[@id="yDmH0d"]/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[2]/div/div[8]/div/div[1]/span[1]'
        try:
            time.sleep(random.uniform(0, 1))  # 设置随机等待时间，防止触发反bot机制
            WebDriverWait(self.browser, 15).until(
                lambda broswer: self.browser.find_element(By.XPATH, xpath))  # 等待翻译结果，超时15秒
            time.sleep(random.uniform(0, 1))  # 设置随机等待时间，防止触发反bot机制
            text = self.browser.find_element(By.XPATH, xpath)
            res = text.text
        except Exception as e:  # 如果超时则不替换，直接写入原句
            print(e, rawtext)
        full_xpath = '/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[1]/div[1]/div/div[1]/span/button'
        try:
            self.browser.find_element(By.XPATH, full_xpath).click()  # 试图通过叉键清空
            # inputArea.click()
            # inputArea.send_keys(Keys.CONTROL, 'a')
            # inputArea.send_keys(Keys.BACKSPACE)
        except:
            self.inputArea.clear()  # 否则直接清空输入框
        # time.sleep(1)  # 等待清空延迟
        # time.sleep(1)
        return strip_breaks(res)


class caiyun(translator):
    def __init__(self, browser):
        self.browser = browser
        browser.get('https://fanyi.caiyunapp.com/')
        print('等待网页加载...')
        time.sleep(5)
        ActionChains(browser).move_by_offset(0, 0).click().perform()
        # inputArea = browser.find_element_by_class_name('textinput')
        self.inputArea = browser.find_element(By.CLASS_NAME, 'textinput')

    def translate(self, rawtext):
        rawtext = strip_breaks(rawtext)
        rawtext = strip_tags(rawtext)
        res = rawtext
        self.inputArea.send_keys(rawtext)
        xpath = '//*[@id="texttarget"]/div/span'
        try:
            # WebDriverWait(browser, 15).until(lambda broswer: browser.find_element_by_xpath(xpath))  #等待翻译结果，超时15秒
            WebDriverWait(self.browser, 15).until(
                lambda broswer: self.browser.find_element(By.XPATH, xpath))  # 等待翻译结果，超时15秒
            # text = browser.find_element_by_xpath(xpath)
            text = self.browser.find_element(By.XPATH, xpath)
            res = text.text
        except Exception as e:  # 如果超时则不替换，直接写入原句
            print(e, rawtext)
        time.sleep(random.uniform(0, 1))  # 设置随机等待时间，防止触发反bot机制
        try:
            # browser.find_element_by_class_name('text-delete').click()  #试图通过叉键清空
            self.inputArea.click()
            self.inputArea.send_keys(Keys.CONTROL, 'a')
            self.inputArea.send_keys(Keys.BACKSPACE)
        except:
            self.inputArea.clear()  # 否则直接清空输入框
        # time.sleep(2)  # 等待清空延迟
        time.sleep(random.uniform(0, 1))
        return strip_breaks(res)


class youdao(translator):
    def __init__(self, browser):
        self.browser = browser
        browser.get('https://fanyi.youdao.com/')
        print('等待网页加载...')
        time.sleep(3)
        # inputArea = browser.find_element_by_id('inputOriginal')
        self.inputArea = browser.find_element(By.ID, 'js_fanyi_input')
        try:
            # 消除弹出的提示框
            browser.find_element(By.XPATH, '//*[@id="inner-box"]/div/div[2]/span').click()
        except:
            pass
        try:
            # 切换到英语
            browser.find_element(By.XPATH, '//*[@id="TextTranslate"]/div[1]/div[1]/div/div/div/div[1]').click()
            en_path = '//*[@id="TextTranslate"]/div[1]/div[1]/div/div/div[2]/div/div/div/div/div[1]/div/div[3]'
            WebDriverWait(browser, 3).until(lambda broswer: self.browser.find_element(By.XPATH, en_path))
            browser.find_element(By.XPATH, en_path).click()
            time.sleep(1)
        except:
            pass

    def translate(self, rawtext):
        rawtext = strip_breaks(rawtext)
        rawtext = strip_tags(rawtext)
        res = rawtext
        self.inputArea.send_keys(rawtext)
        xpath = '//*[@id="js_fanyi_output_resultOutput"]/p/span'
        try:
            WebDriverWait(self.browser, 15).until(
                lambda broswer: self.browser.find_element(By.ID, xpath))  # 等待翻译结果，超时15秒
            # text = browser.find_elements_by_xpath(xpath)
            text = self.browser.find_elements(By.XPATH, xpath)
            joinedtext = ''
            for index in range(len(text)):
                joinedtext += text[index].text
            if joinedtext != '':
                res = joinedtext
        except Exception as e:  # 如果超时则不替换，直接写入原句
            print(e, rawtext)
        time.sleep(random.uniform(0.5, 1))  # 设置随机等待时间，防止触发反bot机制
        try:
            # browser.find_element_by_class_name('input__original_delete').click() #试图通过叉键清空
            self.browser.find_element(By.XPATH,
                                      '/html/body/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[1]/a').click()  # 试图通过叉键清空
        except:
            self.inputArea.clear()  # 否则直接清空输入框
        # time.sleep(1)  # 等待清空延迟
        time.sleep(random.uniform(0.5, 1))
        return strip_breaks(res)


class deepl(translator):
    def __init__(self, browser):
        self.browser = browser
        browser.get('https://www.deepl.com/translator')
        print('等待网页加载...')
        time.sleep(5)
        # inputArea = browser.find_element_by_class_name('lmt__textarea.lmt__source_textarea.lmt__textarea_base_style')
        self.inputArea = browser.find_element(By.CLASS_NAME,
                                              'lmt__textarea.lmt__source_textarea.lmt__textarea_base_style')
        try:
            # 选择翻译语言
            browser.find_element(By.XPATH, '//*[@id="panelTranslateText"]/div[1]/div[2]/section[1]/div[1]/div[2]/button').click()
            en_path = '//*[@id="panelTranslateText"]/div[1]/div[2]/section[1]/div[6]/div[2]/div[3]/button[7]'
            WebDriverWait(browser, 3).until(lambda broswer: self.browser.find_element(By.XPATH, en_path))
            browser.find_element(By.XPATH, en_path).click()
            time.sleep(1)
        except:
            pass

    def translate(self, rawtext):
        rawtext = strip_breaks(rawtext)
        rawtext = strip_tags(rawtext)
        # res = rawtext
        self.inputArea.send_keys(rawtext)
        div_id = 'target-dummydiv'
        try:
            WebDriverWait(self.browser, 15).until(
                lambda broswer: self.browser.find_element(By.XPATH, '//*[@id="panelTranslateText"]/div[1]/div[2]/section[2]/div[3]/div[1]/d-textarea/div/p').text)  # 等待翻译结果，超时15秒
            time.sleep(1)
        except Exception as e:  # 如果超时则不替换，直接写入原句
            print(e, rawtext)
            pass
        time.sleep(2)
        res = self.browser.find_element(By.ID, div_id).get_attribute('innerHTML').strip('\r\n')
        # res = text
        try:
            self.browser.find_element(By.XPATH,
                                      '//*[@id="translator-source-clear-button"]').click()  # 试图通过叉键清空
        except:
            self.inputArea.clear()  # 否则直接清空输入框
        time.sleep(random.uniform(0, 1))
        return strip_breaks(res)

import random
import time
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from .base import translator
from util.misc import strip_tags, strip_breaks


def init_chrome(driver_path):
    options = webdriver.ChromeOptions()
    options.add_argument("window-size=1920x1080")
    print("正在启动chromedriver...")
    # driver_path = r'D:\Users\Surface Book2\Downloads\chromedriver_win32\chromedriver.exe'
    try:
        s = Service(driver_path)
        browser = webdriver.Chrome(service=s, options=options)
    except SessionNotCreatedException as err:
        print(
            "\nchromedriver版本不对，请到 https://registry.npmmirror.com/binary.html?path=chromedriver/ 下载对应版本（Chrome版本信息如下）\n",
            err)
        exit(1)
    return browser


class web_translator(translator):
    def __init__(self, driver_path):
        self.browser = init_chrome(driver_path)

    def close(self):
        try:
            self.browser.quit()
            self.browser.stop_client()
        except Exception as err:
            print(err)


class context_wrapper:
    def __init__(self, trans_obj):
        self.trans_obj = trans_obj

    def __enter__(self):
        return self.trans_obj

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.trans_obj.close()


def wrap_web_trans(trans_obj):
    return context_wrapper(trans_obj)


class google(web_translator):
    def __init__(self, driver_path):
        super().__init__(driver_path)
        self.browser.get('https://translate.google.com/')
        print('等待网页加载...')
        time.sleep(4)
        try:
            # 关闭"继续使用 Google 前须知"框
            self.browser.find_element(By.XPATH,
                                      '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div/button').click()
            time.sleep(1)
        except:
            pass
        try:
            # 切换到英语
            self.browser.find_element(By.XPATH,
                                      '/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[1]/c-wiz/div[1]/c-wiz/div[2]/div/div[2]/div/div/span/button[2]').click()
            time.sleep(1)
        except:
            pass
        time.sleep(2)
        self.inputArea = self.browser.find_element(By.XPATH,
                                                   '//*[@id="yDmH0d"]/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[1]/span/span/div/textarea')

    def translate(self, rawtext):
        res = strip_breaks(rawtext)
        res = strip_tags(res)
        self.inputArea.send_keys(res)
        xpath = '/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div/div[2]/div[3]/c-wiz[2]/div/div[9]/div/div[1]'
        success = False
        try:
            time.sleep(random.uniform(0, 1))  # 设置随机等待时间，防止触发反bot机制
            WebDriverWait(self.browser, 15).until(
                lambda broswer: self.browser.find_element(By.XPATH, xpath))  # 等待翻译结果，超时15秒
            text = self.browser.find_element(By.XPATH, xpath)
            res = text.text
            success = True
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
        # time.sleep(2)  # 等待清空延迟
        time.sleep(random.uniform(0.2, 1))
        if not success:
            return rawtext
        # time.sleep(1)  # 等待清空延迟
        # time.sleep(1)
        return strip_breaks(res)


class caiyun(web_translator):
    def __init__(self, driver_path):
        super().__init__(driver_path)
        self.browser.get('https://fanyi.caiyunapp.com/')
        print('等待网页加载...')
        time.sleep(5)
        ActionChains(self.browser).move_by_offset(0, 0).click().perform()
        # inputArea = browser.find_element_by_class_name('textinput')
        self.inputArea = self.browser.find_element(By.CLASS_NAME, 'textinput')

    def translate(self, rawtext):
        res = strip_breaks(rawtext)
        res = strip_tags(res)
        self.inputArea.send_keys(res)
        xpath = '//*[@id="texttarget"]/div/span'
        success = False
        try:
            # 点击翻译按钮
            self.browser.find_element(By.XPATH, '//*[@id="app"]/div[2]/div[1]/div[2]/div/div[1]/div[3]').click()
            time.sleep(random.uniform(0, 1))  # 设置随机等待时间，防止触发反bot机制
            # WebDriverWait(browser, 15).until(lambda broswer: browser.find_element_by_xpath(xpath))  #等待翻译结果，超时15秒
            WebDriverWait(self.browser, 15).until(
                lambda broswer: self.browser.find_element(By.XPATH, xpath))  # 等待翻译结果，超时15秒
            # text = browser.find_element_by_xpath(xpath)
            text = self.browser.find_element(By.XPATH, xpath)
            res = text.text
            success = True
        except Exception as e:  # 如果超时则不替换，直接写入原句
            print(e, rawtext)
        try:
            # browser.find_element_by_class_name('text-delete').click()  #试图通过叉键清空
            self.inputArea.click()
            self.inputArea.send_keys(Keys.CONTROL, 'a')
            self.inputArea.send_keys(Keys.BACKSPACE)
        except:
            self.inputArea.clear()  # 否则直接清空输入框
        # time.sleep(2)  # 等待清空延迟
        time.sleep(random.uniform(0.2, 1))
        if not success:
            return rawtext
        return strip_breaks(res)

def wait_until_no_appending(browser, by, value, wait_time=0.1):
    WebDriverWait(browser, 15).until(
        lambda b: b.find_element(by, value))  # 等待翻译结果，超时15秒
    pre = -1
    cur = len(browser.find_elements(by, value))
    while cur != pre:
        pre = cur
        time.sleep(wait_time)
        cur = len(browser.find_elements(by, value))

class youdao(web_translator):
    def __init__(self, driver_path):
        super().__init__(driver_path)
        self.browser.get('https://fanyi.youdao.com/')
        print('等待网页加载...')
        time.sleep(3)
        # inputArea = browser.find_element_by_id('inputOriginal')
        self.inputArea = self.browser.find_element(By.ID, 'js_fanyi_input')
        try:
            # 消除弹出的提示框
            self.browser.find_element(By.XPATH, '/html/body/div[4]/div/img[2]').click()
        except:
            pass
        try:
            # 消除弹出的提示框
            self.browser.find_element(By.XPATH, '//*[@id="inner-box"]/div/div[2]/span').click()
        except:
            pass
        try:
            # 切换到英语
            self.browser.find_element(By.XPATH, '//*[@id="TextTranslate"]/div[1]/div[1]/div/div/div/div[1]').click()
            en_path = '//*[@id="TextTranslate"]/div[1]/div[1]/div/div/div[2]/div/div/div/div/div[1]/div/div[3]'
            WebDriverWait(self.browser, 3).until(lambda broswer: self.browser.find_element(By.XPATH, en_path))
            self.browser.find_element(By.XPATH, en_path).click()
            time.sleep(1)
        except:
            pass


    def translate(self, rawtext):
        res = strip_breaks(rawtext)
        res = strip_tags(res)
        self.inputArea.send_keys(res)
        xpath = '//*[@id="js_fanyi_output_resultOutput"]/p/span'
        time.sleep(random.uniform(0, 1))  # 设置随机等待时间，防止触发反bot机制
        success = False
        try:
            wait_until_no_appending(self.browser, By.XPATH, xpath)
            text = self.browser.find_element(By.XPATH, '//*[@id="js_fanyi_output_resultOutput"]/p').text
            # joinedtext = ''
            # for index in range(len(text)):
            #     joinedtext += text[index].text
            # if joinedtext != '':
            res = text
            success = True
        except Exception as e:  # 如果超时则不替换，直接写入原句
            print(e, rawtext)
        try:
            # browser.find_element_by_class_name('input__original_delete').click() #试图通过叉键清空
            self.browser.find_element(By.XPATH,
                                      '/html/body/div[1]/div[1]/div[2]/div[2]/div/div[1]/div/div[1]/a').click()  # 试图通过叉键清空
        except:
            self.inputArea.clear()  # 否则直接清空输入框
        # time.sleep(1)  # 等待清空延迟
        time.sleep(random.uniform(0.2, 1))
        if not success:
            return rawtext
        return strip_breaks(res)

def wait_until_no_extending(browser, by, value, wait_time=0.1):
    WebDriverWait(browser, 15).until(
        lambda b: b.find_element(by, value))  # 等待翻译结果，超时15秒
    pre = -1
    cur = len(browser.find_element(by, value).text)
    while cur != pre:
        pre = cur
        time.sleep(wait_time)
        cur = len(browser.find_element(by, value).text)

class deepl(web_translator):
    def __init__(self, driver_path):
        super().__init__(driver_path)
        self.browser.get('https://www.deepl.com/zh/translator')
        print('等待网页加载...')
        time.sleep(5)
        # inputArea = browser.find_element_by_class_name('lmt__textarea.lmt__source_textarea.lmt__textarea_base_style')
        self.inputArea = self.browser.find_element(By.CLASS_NAME,
                                                   'lmt__textarea.lmt__source_textarea.lmt__textarea_base_style')
        try:
            # 选择翻译语言
            self.browser.find_element(By.XPATH,
                                      '//*[@id="panelTranslateText"]/div[1]/div[2]/section[1]/div[1]/div[2]/button').click()
            en_path = '//*[@id="panelTranslateText"]/div[1]/div[2]/section[1]/div[6]/div[2]/div[3]/button[7]'
            WebDriverWait(self.browser, 3).until(lambda broswer: self.browser.find_element(By.XPATH, en_path))
            self.browser.find_element(By.XPATH, en_path).click()
            time.sleep(1)
        except:
            pass

    def translate(self, rawtext):
        res = strip_breaks(rawtext)
        res = strip_tags(res)
        self.inputArea.send_keys(res)
        div_id = 'target-dummydiv'
        xpath = '//*[@id="panelTranslateText"]/div[1]/div[2]/section[2]/div[3]/div[1]/d-textarea/div/p'
        time.sleep(random.uniform(0, 1))
        success = False
        try:
            wait_until_no_extending(self.browser, By.XPATH, xpath, wait_time=0.7)
            res = self.browser.find_element(By.ID, div_id).get_attribute('innerHTML').strip()
            success = True
        except Exception as e:  # 如果超时则不替换，直接写入原句
            print(e, rawtext)
            pass
        # res = text
        try:
            self.browser.find_element(By.XPATH,
                                      '//*[@id="translator-source-clear-button"]').click()  # 试图通过叉键清空
        except:
            self.inputArea.clear()  # 否则直接清空输入框
        time.sleep(random.uniform(0.2, 1))
        if not success:
            return rawtext
        return strip_breaks(res)

class baidu(web_translator):
    def __init__(self, driver_path):
        super().__init__(driver_path)
        self.browser.get('https://fanyi.baidu.com/?aldtype=16047#en/zh/')
        print('等待网页加载...')
        time.sleep(5)
        ActionChains(self.browser).move_by_offset(0, 0).click().perform()
        # inputArea = browser.find_element_by_class_name('textinput')
        try:
            # 消除弹出的提示框
            self.browser.find_element(By.XPATH, '//*[@id="app-guide"]/div/div/div[2]/span').click()
        except:
            pass
        self.inputArea = self.browser.find_element(By.ID, 'baidu_translate_input')

    def translate(self, rawtext):
        res = strip_breaks(rawtext)
        res = strip_tags(res)
        self.inputArea.send_keys(res)
        xpath = '//*[@id="main-outer"]/div/div/div[1]/div[2]/div[1]/div[2]/div/div/div[1]/p[2]'
        success = False
        try:
            # if '.' not in res or '?' not in res or '!' not in res:
            #     res += '.'
            # 点击翻译按钮
            self.browser.find_element(By.ID, 'translate-button').click()
            time.sleep(random.uniform(0, 1))  # 设置随机等待时间，防止触发反bot机制
            wait_until_no_extending(self.browser, By.XPATH, xpath, wait_time=0.7)
            res = self.browser.find_element(By.XPATH, xpath).text.strip()
            success = True
        except Exception as e:  # 如果超时则不替换，直接写入原句
            print(e, rawtext)
        try:
            # browser.find_element_by_class_name('input__original_delete').click() #试图通过叉键清空
            self.browser.find_element(By.XPATH,
                                      '//*[@id="main-outer"]/div/div/div[1]/div[2]/div[1]/div[1]/div/div[2]/a').click()  # 试图通过叉键清空
        except:
            self.inputArea.clear()  # 否则直接清空输入框
        # time.sleep(1)  # 等待清空延迟
        time.sleep(random.uniform(0.2, 1))
        if not success:
            return rawtext
        return strip_breaks(res)
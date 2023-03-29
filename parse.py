import argparse
import glob
import os.path as osp
import re
import time

import numpy as np
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm

import trans_engine
from file import exists_file, file_name, mkdir, exists_dir


class replacer:
    def __init__(self, target_file, save_dir):
        with open(target_file, 'r', encoding='utf-8') as f:
            self.data = f.readlines()
        assert exists_file(target_file)
        self.save_file = osp.join(save_dir, file_name(target_file))
        self.start_idx = 0
        if exists_file(self.save_file):
            with open(self.save_file, 'r', encoding='utf-8') as f:
                temp_data = f.readlines()
                self.start_idx = len(temp_data)

    def start(self, force=False):
        if force:
            self.start_idx = 0
            self.file_handle = open(self.save_file, 'w', encoding='utf-8', newline='')
        else:
            if self.start_idx < len(self.data):
                self.file_handle = open(self.save_file, 'a', encoding='utf-8', newline='')
        return self.start_idx < len(self.data)

    def cur_line(self):
        return self.start_idx + 1

    def __len__(self):
        return len(self.data)

    def next(self):
        if self.start_idx < len(self.data):
            return self.data[self.start_idx]
        else:
            if hasattr(self, "file_handle"):
                self.file_handle.close()
        return None

    def update(self, text):
        if self.start_idx < len(self.data):
            self.file_handle.write(text)
            self.start_idx += 1
            if np.random.rand() > 0.99:
                self.file_handle.flush()


# match the variable
regex_var = re.compile(r'(\[[A-Za-z_]+[A-Za-z1-9_]*\])')


def parse_text(text: str, translator=None):
    if not ('old "' in text or 'translate ' in text or '# ' in text or text == '\n'):
        first_quote = text.find("\"")
        last_quote = text.rfind("\"")
        if first_quote == last_quote:
            return text
        raw_text = text[first_quote + 1:last_quote]
        if raw_text.strip() == "":
            return text
        res = regex_var.findall(raw_text)
        # replace the var by another name
        tmp_res = [f'T{i}V' for i in range(len(res))]
        for i in range(len(res)):
            raw_text = raw_text.replace(res[i], tmp_res[i])
        if translator:
            raw_text = translator.translate(raw_text)
        for i in range(len(res)):
            raw_text = raw_text.replace(tmp_res[i], res[i])
            raw_text = raw_text.replace(tmp_res[i].lower(), res[i])
        return text.replace(text[first_quote + 1:last_quote], raw_text)
    return text


def parse_file(rpy_file, save_dir, translator):
    r = replacer(rpy_file, save_dir)
    if r.start():
        with tqdm(total=len(r) - r.cur_line() + 1) as pbar:
            text = r.next()
            while text is not None:
                new_text = parse_text(text, translator)
                r.update(new_text)
                pbar.update(1)
                pbar.set_description(f'cur line:{r.cur_line()}/{len(r)}')
                text = r.next()


def parse_files(rpy_files, save_dir, translator):
    for i, rpy_file in enumerate(rpy_files):
        print(f'current file: {i + 1}/{len(rpy_files)}：{rpy_file}')
        if exists_file(rpy_file):
            parse_file(rpy_file, save_dir, translator)
        else:
            print(f'skipping the nonexistent file:{rpy_file}')


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


def main():
    time_start = time.time()
    print("RenPy翻译文件机翻工具")
    print("By Koshiro, version 1.4")
    # print("使用前请确认待翻译文件trans.txt已放在本目录")
    parser = argparse.ArgumentParser(prog="name", description="description")
    parser.add_argument(
        "files",
        metavar="FILENAME/DIRNAME",
        type=str,
        help="the rpy(s) or dir(s) containing rpy(s) to translate.",
        nargs="+",
    )
    parser.add_argument(
        "--driver",
        type=str,
        required=True,
        help="the executable path for the chrome driver",
    )
    parser.add_argument(
        "-t",
        "--trans_api",
        type=str,
        default='google',
        choices=['caiyun', 'youdao', 'deepl', 'google'],
        help="the translation API to use",
    )
    parser.add_argument(
        "-s",
        "--save",
        type=str,
        default='./translated',
        help="save dir for translated rpy(s)",
    )
    args = parser.parse_args()
    print(args)
    # create the dir of translated files
    mkdir(args.save)
    # build the browser
    browser = init_chrome(args.driver)
    # build the selected translator
    translator = trans_engine.__dict__[args.trans_api](browser)
    # parse each file/dir in each given files/dirs
    for i, rpy_dir in enumerate(args.files):
        print(f'current dir: {i + 1}/{len(args.files)}：{rpy_dir}')
        if exists_dir(rpy_dir):
            rpy_files = sorted(glob.glob(osp.join(rpy_dir, "*.rpy")))
            # using the last name of rpy_dir as the subdir of save_dir
            save_dir = osp.join(args.save, osp.basename(rpy_dir))
            mkdir(save_dir)
            parse_files(rpy_files, save_dir, translator)
        elif exists_file(rpy_dir):
            # parse given files
            parse_files([rpy_dir], args.save, translator)
        else:
            print(f'skipping the nonexistent item:{rpy_dir}')
    browser.quit()
    browser.stop_client()
    time_end = time.time()
    print("生成完毕，耗时{:.0f}min".format((time_end - time_start) / 60))
    # input("按回车键退出")


if __name__ == '__main__':
    main()

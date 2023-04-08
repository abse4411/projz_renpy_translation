import argparse
import glob
import os.path as osp
import time

import numpy as np

from tqdm import tqdm

from trans import web_trans
from trans.web_trans import wrap_web_trans
from util.file import exists_file, file_name, mkdir, exists_dir
from util.misc import var_list, text_type, TEXT_TYPE, is_empty, replacer


def parse_text(text: str, translator=None):
    raw_text, ttype = text_type(text)
    if ttype == TEXT_TYPE.NEW:
        # if raw text is empty, just return original text
        if is_empty(raw_text):
            return text
        new_txt = raw_text.strip()
        # the new text starts with "@$" which marked in the previous phase is required translation
        if new_txt[:2] == '@$':
            new_txt = new_txt[2:]
        else:
            return text
        res = var_list(new_txt)
        # replace the var by another name
        tmp_res = [f'TC{i}X' for i in range(len(res))]
        for i in range(len(res)):
            new_txt = new_txt.replace(res[i], tmp_res[i])
        trans_txt = new_txt
        if translator:
            trans_txt = translator.translate(new_txt)
        # if new txt is not translated, just return original text
        if trans_txt == new_txt:
            return text
        # replace the var back
        for i in range(len(res)):
            trans_txt = trans_txt.replace(tmp_res[i], res[i])
            trans_txt = trans_txt.replace(tmp_res[i].lower(), res[i])
        return text.replace(raw_text, trans_txt)
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





def main():
    time_start = time.time()
    print("RenPy rpy文件机翻工具")
    print("By abse4411(Github), version 1.0")
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
    # build the selected translator
    with wrap_web_trans(web_trans.__dict__[args.trans_api](args.driver)) as translator:
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
    time_end = time.time()
    print("生成完毕，耗时{:.0f}min".format((time_end - time_start) / 60))
    # input("按回车键退出")


if __name__ == '__main__':
    main()

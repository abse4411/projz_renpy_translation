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
from misc import var_list, text_type, TEXT_TYPE, replacer, contain_alpha, is_empty

def get_translated_text(rpy_file):
    with open(rpy_file, 'r', encoding='utf-8') as f:
        temp_data = f.readlines()
    res = dict()
    raw_text = None
    raw_line = -1
    # new_text = None
    for i, line in enumerate(temp_data, 1):
        text, ttype = text_type(line)
        if ttype == TEXT_TYPE.RAW:
            if is_empty(text):
                print(f'=========================>warning, the empty raw text({text}) in line {i} is skipped!')
                raw_text = None
                raw_line = -1
                continue
            assert raw_text is None, f"unmatched raw text({text}) in line {i}, last raw text is \"{raw_text}\""
            raw_text = text
            raw_line = i
        if ttype == TEXT_TYPE.NEW:
            if not is_empty(text):
                # raw text and new text must appear in pairs
                assert raw_text is not None and i - raw_line == 1, f"unmatched new text({text}) in line {i}. raw text({raw_text}, line {raw_line}) "
                res[raw_text] = text
                raw_text = None
                raw_line = -1
            else:
                if not is_empty(raw_text) and i - raw_line == 1:
                    print(
                        f'=========================>warning, the empty new text({text}) in line {i} is replaced by raw text({raw_text}) of line {raw_line}')
                    res[raw_text] = text
                    raw_text = None
                    raw_line = -1
                else:
                    print(f'=========================>warning, the empty new text({text}) in line {i} is skipped!')
    return res


def main():
    time_start = time.time()
    print("RenPy翻译文件机翻工具")
    print("By Koshiro, version 1.4")
    # print("使用前请确认待翻译文件trans.txt已放在本目录")
    parser = argparse.ArgumentParser(prog="name", description="description")
    parser.add_argument(
        "-o",
        "--old-dir",
        type=str,
        default='./old',
        help="the dir containing translated rpy(s) from old version",
    )
    parser.add_argument(
        "-n",
        "--new-dir",
        type=str,
        default='./new',
        help="the dir containing untranslated rpy(s)",
    )
    parser.add_argument(
        "-s",
        "--save",
        type=str,
        default='./tmp',
        help="save dir for translated rpy(s)",
    )
    args = parser.parse_args()
    print(args)
    # create the dir of translated files
    mkdir(args.save)

    # get rpy files from new dir
    new_rpy_files = sorted(glob.glob(osp.join(args.new_dir, "*.rpy")))
    new_rpy_files = [file_name(f) for f in new_rpy_files]
    # get rpy files from old dir
    # old_rpy_files = sorted(glob.glob(osp.join(args.old_dir, "*.rpy")))
    # old_rpy_files = [file_name(f) for f in old_rpy_files]

    tot_untrans_count, tot_trans_count = 0, 0
    with open(osp.join('./tran_summary.txt'), 'w', encoding='utf-8', newline='\n') as summary:
        summary.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}\n")
        for i, rpy_file in enumerate(new_rpy_files):
            print(f'current file: {i + 1}/{len(new_rpy_files)}：{rpy_file}')
            new_rpy = osp.join(args.new_dir, rpy_file)
            old_rpy = osp.join(args.old_dir, rpy_file)
            # get translated text from old version rpy
            if exists_file(old_rpy):
                translated_text = get_translated_text(old_rpy)
            else:
                print(f'{old_rpy} not found, no translated text is available.')
                translated_text = dict()
            # build the selected translator
            translator = trans_engine.__dict__["dict_translator"](translated_text)
            r = replacer(new_rpy, args.save)
            untrans_count, trans_count = 0, 0
            # start translation
            r.start(force=True)
            text = r.next()
            while text is not None:
                updated_text = text
                raw_text, ttype = text_type(text)
                # if the line is new text (requiring translation)
                if ttype == TEXT_TYPE.NEW:
                    striped_text = raw_text.strip()
                    # if the raw text is not empty or blank
                    if striped_text:
                        tran_text = translator.translate(raw_text)
                        # if raw text is not translated in old rpy, or contains alphas
                        if tran_text == raw_text and contain_alpha(raw_text):
                            # add special marks to the untranslated text,
                            # please remove these marks before translating the raw text in the next phase
                            tran_text = "@$" + raw_text
                            untrans_count += 1
                        else:
                            # count translated lines
                            trans_count += 1
                    else:
                        # keep it, there is no translation required
                        tran_text = raw_text
                        untrans_count += 1
                    # replace the raw_text with the translated text if possible
                    updated_text = updated_text.replace(raw_text, tran_text)
                r.update(updated_text)
                text = r.next()
            print_text = f'{rpy_file}[total line(s):{trans_count + untrans_count}] is translated with {trans_count} translated line(s) and {untrans_count} untranslated line(s).'
            print(print_text)
            summary.write(print_text)
            summary.write('\n')
            tot_trans_count += trans_count
            tot_untrans_count += untrans_count
        print_text = f'{len(new_rpy_files)} rpy files are translated with {tot_trans_count} translated line(s) and {tot_untrans_count} untranslated line(s).'
        print(print_text)
        summary.write(print_text)
        summary.write('\n')

    time_end = time.time()
    print("生成完毕，耗时{:.0f}min".format((time_end - time_start) / 60))
    # input("按回车键退出")


if __name__ == '__main__':
    main()

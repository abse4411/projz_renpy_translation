import argparse
import glob
import os.path as osp
import time

from util.file import exists_file, file_name, mkdir
from util.misc import text_type, TEXT_TYPE, replacer


def main():
    time_start = time.time()
    print("RenPy rpy文件机翻工具")
    print("By abse4411(Github), version 1.0")
    # print("使用前请确认待翻译文件trans.txt已放在本目录")
    parser = argparse.ArgumentParser(prog="name", description="description")
    parser.add_argument(
        "-o",
        "--old-dir",
        type=str,
        default='./source',
        help="the dir containing translated rpy(s) to revert",
    )
    parser.add_argument(
        "-s",
        "--save",
        type=str,
        default='./reverted',
        help="save dir for translated rpy(s)",
    )
    args = parser.parse_args()
    print(args)
    # create the dir of translated files
    mkdir(args.save)

    # get source files from new dir
    new_rpy_files = sorted(glob.glob(osp.join(args.old_dir, "*.rpy")))
    new_rpy_files = [file_name(f) for f in new_rpy_files]
    # get rpy files from old dir
    # old_rpy_files = sorted(glob.glob(osp.join(args.old_dir, "*.rpy")))
    # old_rpy_files = [file_name(f) for f in old_rpy_files]

    tot_untrans_count, tot_trans_count = 0, 0

    for i, rpy_file in enumerate(new_rpy_files):
        print(f'current file: {i + 1}/{len(new_rpy_files)}：{rpy_file}')
        old_rpy = osp.join(args.old_dir, rpy_file)
        # get translated text from old version rpy
        if exists_file(old_rpy):
            r = replacer(old_rpy, args.save)
            untrans_count, trans_count = 0, 0
            # start translation
            r.start(force=True)
            text = r.next()
            raw_text = None
            raw_line = -1
            while text is not None:
                updated_text = text
                cur_text, ttype = text_type(text)
                # if the line is new text (requiring translation)
                if ttype == TEXT_TYPE.RAW:
                    raw_text = cur_text
                    raw_line = r.cur_line()
                if ttype == TEXT_TYPE.NEW:
                    assert raw_text is not None and r.cur_line() - raw_line == 1, f"unmatched new text({text}) in line {r.cur_line()}. raw text({raw_text}, line {raw_line}) "
                    updated_text = updated_text.replace(cur_text, raw_text)
                    raw_text = None
                    raw_line = -1
                r.update(updated_text)
                text = r.next()
        else:
            print(f'{old_rpy} not found, no translated text is available.')


    time_end = time.time()
    print("生成完毕，耗时{:.0f}min".format((time_end - time_start) / 60))
    # input("按回车键退出")


if __name__ == '__main__':
    main()

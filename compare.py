import argparse
import glob
import os.path as osp
import re
import time

from trans.base import translator
from util.file import exists_file, file_name, mkdir
from util.misc import text_type, TEXT_TYPE, replacer, contain_alpha, is_empty
import pandas as pd

class rwa_item:
    def __init__(self, line, code, source, raw_text):
        self.line = line
        self.code = code
        self.source = source
        self.raw_text = raw_text

# 匹配这种格式的字符串:"# "That’s a fair assessment.""
# 匹配这种格式的字符串:"# s "That’s a fair assessment.""
# 匹配这种格式的字符串:"old "That’s a fair assessment.""
regex_raw = re.compile(r'^\s+(?:old |# )[^"]*"([^\r\n]*)')
# 匹配原始这种格式的符串:"# renpy/common/00accessibility.rpy:138"
regex_code = re.compile(r'\s*#\s*([^\r\n]*)(?=\.rpy[^:\r\n]*:)([^\r\n]*)')
# 匹配字符串这种格式的字符串:"translate chinese nikiinvite2_442941ca_1:"
regex_trans = re.compile(r'^translate chinese ([^\r\n:]*):')

raw_match_texts = [
    '    old "Line 0Spacing Scaling"\n',
    '    old "Line 1Spacing Scaling\n',
    '    # "Line 3Spacing Scaling"\n',
    '    # "Line 4Spacing Scaling\n',
    '    # old "Line 5Spacing Scaling"\n',
    '    # old "Line 6Spacing Scaling\n',
    '    # old "Line 7"Spacing" Scaling"\n',
    '    # old "Line 8"Spacing" Scaling\n',
    '    # old "Line 9"Spacing" Scaling""\n',
]

raw_unmatch_texts = [
    '    ni "Line 0Spacing"\n',
    '    ni "Line 1Spacing\n',
    '    oldd "Line 3Spacing"\n',
    '    oldd "Line 4Spacing \n',
    '    new "Line 5Spacing"\n',
    '    new "Line 6Spacing\n',
    '    "Line 7Spacing"\n',
    '    "Line 8Spacing\n',
]

code_matchtexts = [
    '# game/AyaneEvents.rpy:584\n',
    '   # game/AyaneEvents.rpy:584\n',
    '# game/AyaneEvents.rpym:584\n',
    '   # game/AyaneEvents.rpym:?465\n',
]


def unit_test(regrex, match_arr, unmatch_arr):
    print(f'================>单元测试：正则表达式:r"{regrex.pattern}"<================')
    for i, t in enumerate(match_arr):
        res = regrex.search(t)
        if res:
            assert len(res.group(1)) > 1, f'正用例{i}({t})无法通过，匹配结果：|{res.group(1)}|'
            print(f'通过正用例{i}({t})，匹配结果：|{res.group(1)}|')
        else:
            assert False, f'正用例{i}({t})无法通过，匹配结果：|{res}|'
    for i, t in enumerate(unmatch_arr):
        res = regrex.search(t)
        assert res is None, f'负用例{i}({t})无法通过，匹配结果：|{res.group(1)}|'
        print(f'通过负用例{i}({t})，匹配结果：|{res}|')
    print('================>测试通过<================')


unit_test(regex_raw, raw_match_texts, raw_unmatch_texts)
unit_test(regex_code, code_matchtexts, raw_unmatch_texts + raw_unmatch_texts)

def get_translated_text(rpy_file):
    with open(rpy_file, 'r', encoding='utf-8') as f:
        temp_data = f.readlines()
    # res = dict()
    raw_text, raw_line = None, -1
    code_text, code_line = None, -1
    trans_text, tran_line = None, -1

    res_dict = dict()
    # new_text = None
    i = 0
    while i < len(temp_data):
        line = temp_data[i]
        match_trans = regex_trans.search(line)
        if match_trans:
            trans_text, tran_line = match_trans.group(1), i
            # 如果匹配到这种文本：
            '''
            translate chinese strings:

                # renpy/common/00accessibility.rpy:28
                old "Self-voicing disabled."
                new "自动发声已禁用。"
            '''
            #
            if trans_text == "strings":
                while i+1<len(temp_data):
                    i += 1
                    line = temp_data[i]
                    match_trans = regex_trans.search(line)
                    # 如果匹配到这种文本该跳出了：translate chinese callnikiafternoon_7c40cbf0:
                    if match_trans:
                        i -= 1
                        line = ''
                        break
                    # 如果匹配这种文本:     # "I tap on Niki’s name in my phone and wait for her to answer."
                    match_raw = regex_raw.search(line)
                    if match_raw:
                        raw_text, raw_line = match_raw.group(1), i
                        # 手动去除最后一个引号
                        if raw_text and raw_text[-1] == "\"":
                            raw_text = raw_text[:-1]
                        assert raw_line - code_line < 2, f'{rpy_file}:code行({code_text},line{code_line + 1})和raw_text行({raw_text},line{raw_line + 1})相隔太远'
                        assert code_text
                        # 这对这种重复的code行：
                        '''
                        translate chinese strings:

                            # game/AyaneEvents.rpy:70
                            old "Laying"
                            new "Laying"
                        
                            # game/AyaneEvents.rpy:70
                            old "Raise"
                            new "Raise"
                        '''
                        if code_text in res_dict:
                            # 添加自定义后缀
                            if code_text.rfind('_') == len(code_text) - 1:
                                num_str =code_text[code_text.rfind('_')+1:]
                                num = int(num_str)
                                num += 1
                                code_text = code_text[:code_text.rfind('_')+1] + str(num)
                            else:
                                code_text += "_0"

                        # 保存信息
                        res_dict[code_text] = rwa_item(i + 1, code_text, trans_text, raw_text)
                        # 清空匹配的code_text和trans_text
                        code_text, code_line = None, -1
                        # trans_text, tran_line = None, -1
                        line = ''
                    # 如果匹配这种文本:     # game/NikiEvents.rpy:16
                    match_code = regex_code.search(line)
                    if match_code:
                        code_text, code_line = ''.join(match_code.groups()), i
            else:
                # 否则就是这种文本：
                '''
                # TODO: Translation updated at 2022-09-16 19:37
                # game/NikiEvents.rpy:15
                translate chinese callnikiafternoon_7c40cbf0:
                
                    # "I tap on Niki’s name in my phone and wait for her to answer."
                    "我点开手机里Niki的名字，等待她的回答。"
                '''
                # trans_text, tran_line = match_trans.group(1), i
                line = ''
        # 如果匹配这种文本:     # "I tap on Niki’s name in my phone and wait for her to answer."
        match_raw = regex_raw.search(line)
        if match_raw:
            raw_text, raw_line = match_raw.group(1), i
            # 手动去除最后一个引号
            if raw_text and raw_text[-1] == "\"":
                raw_text = raw_text[:-1]
            if not raw_line - tran_line < 4:
                print(f'{rpy_file}:translate行({trans_text},line{tran_line+1})和raw_text行({raw_text},line{raw_line+1})相隔太远')
                pass
            assert raw_line - tran_line < 4, f'{rpy_file}:translate行({trans_text},line{tran_line+1})和raw_text行({raw_text},line{raw_line+1})相隔太远'
            assert raw_line - code_line < 4, f'{rpy_file}:code行({code_text},line{code_line+1})和raw_text行({raw_text},line{raw_line+1})相隔太远'
            assert trans_text and trans_text not in res_dict
            # 保存信息
            res_dict[trans_text] = rwa_item(i+1, code_text, trans_text, raw_text)
            # 清空匹配的code_text和trans_text
            code_text, code_line = None, -1
            trans_text, tran_line = None, -1
            line = ''
            pass
        # 如果匹配这种文本:     # game/NikiEvents.rpy:16
        match_code = regex_code.search(line)
        if match_code:
            code_text, code_line =''.join(match_code.groups()), i
        i += 1
    return res_dict


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
        default='./old_ver',
        help="the dir containing translated rpy(s) from old version",
    )
    parser.add_argument(
        "-n",
        "--new-dir",
        type=str,
        default='./new_ver',
        help="the dir containing untranslated rpy(s)",
    )
    parser.add_argument(
        "-s",
        "--save",
        type=str,
        default='./fc_res',
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

    excel_writer = pd.ExcelWriter(osp.join(args.save, f"FC{time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))}.xlsx"))
    tot_untrans_count, tot_trans_count = 0, 0
    # with open(osp.join('./fc.txt'), 'w', encoding='utf-8', newline='\n') as summary:
    # summary.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}\n")
    for i, rpy_file in enumerate(new_rpy_files):
        print(f'current file: {i + 1}/{len(new_rpy_files)}：{rpy_file}')
        new_rpy = osp.join(args.new_dir, rpy_file)
        old_rpy = osp.join(args.old_dir, rpy_file)
        trans_count, untrans_count = 0, 0
        if exists_file(new_rpy) and exists_file(old_rpy):
            old_dict = get_translated_text(old_rpy)
            new_dict = get_translated_text(new_rpy)
            excel_data = {
                '原文件所在行数':[],
                '新文件所在行数': [],
                '原翻译索引':[],
                '新翻译索引': [],
                '原代码索引':[],
                '新代码索引': [],
                '原内容':[],
                '新内容': [],
            }
            for ok,ov in old_dict.items():
                if ok in new_dict:
                    nv = new_dict[ok]
                    if nv.raw_text.strip() != ov.raw_text.strip():
                        excel_data['原文件所在行数'].append(ov.line)
                        excel_data['原翻译索引'].append(ov.source)
                        excel_data['原代码索引'].append(ov.code)
                        excel_data['原内容'].append(ov.raw_text)
                        excel_data['新内容'].append(nv.raw_text)
                        excel_data['新翻译索引'].append(nv.source)
                        excel_data['新代码索引'].append(nv.code)
                        excel_data['新文件所在行数'].append(nv.line)
            if len(excel_data['原文件所在行数']) > 0:
                pddata = pd.DataFrame(excel_data)
                pddata.to_excel(excel_writer=excel_writer,sheet_name=file_name(new_rpy))
        else:
            print(f'文件（{new_rpy}）或文件（{old_rpy}）不存在，已经跳过')
        tot_trans_count += trans_count
        tot_untrans_count += untrans_count
    excel_writer.save()
    # excel_writer.close()
    print_text = f'{len(new_rpy_files)} rpy files are translated with {tot_trans_count} translated line(s) and {tot_untrans_count} untranslated line(s).'
    print(print_text)


    time_end = time.time()
    print("生成完毕，耗时{:.0f}min".format((time_end - time_start) / 60))
    # input("按回车键退出")


if __name__ == '__main__':
    main()
    pass

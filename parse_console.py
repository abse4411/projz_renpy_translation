import distutils
import glob
import logging
import os.path
import sys
from collections import defaultdict
from typing import List

import prettytable

import log.logger
from cmd import register_cmd, execute_cmd, exists_cmd, all_cmds
from config.config import default_config, CONFIG_FILE

from prettytable import PrettyTable

from store.file_store import save_to_html, load_from_html, load_from_excel, save_to_excel
from store.index import project_index
from util.file import exists_dir, file_name, exists_file, mkdir
from util.misc import my_input, yes

__VERSION__ = '0.3.8a'


def help_cmd():
    print(fr'''________  ________  ________        ___  ________     
|\   __  \|\   __  \|\   __  \      |\  \|\_____  \    
\ \  \|\  \ \  \|\  \ \  \|\  \     \ \  \\|___/  /|   
 \ \   ____\ \   _  _\ \  \\\  \  __ \ \  \   /  / /   
  \ \  \___|\ \  \\  \\ \  \\\  \|\  \\_\  \ /  /_/__  
   \ \__\    \ \__\\ _\\ \_______\ \________\\________\
    \|__|     \|__|\|__|\|_______|\|________|\|_______|   V{__VERSION__}''')
    print("RenPy翻译 rpy翻译文件机翻工具 - translator for Renpy rpy files, renpy translation, rpy translation")
    print(f"By abse4411(https://github.com/abse4411/projz_renpy_translation)")
    table = PrettyTable(['Command', 'Usage', 'Help'])
    table.hrules = prettytable.ALL
    table.add_row(['new or n', 'new {tl_path} {name} {tag} or\nnew {tl_path} {name} {tag} {greedy=True}',
                   'Create an untranslated index from the translation dir ({tl_path}) in renpy.\n It may like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as untranslated ones.\n The {name} and {tag} are using while saving.]\n'
                   'The argument {greedy} is optional, or specify it by True to scan more translation item,\n'
                   'which also discard less invalid lines. Default as True.'])
    table.add_row(['old or o', 'old {tl_path} {name} {tag} or\nold {tl_path} {name} {tag} {greedy=True}',
                   'Create a translated index from the translation dir ({tl_path}) in renpy.\n It may like: D:\\my_renpy\game\\tl\\chinese.'
                   ' All texts are regard as translated ones.\n The {name} and {tag} are using while saving.\n'
                   'The argument {greedy} is optional, or specify it by True to scan more translation item,\n'
                   'which also discard less invalid lines. Default as True.'])
    table.add_row(['reold or ro', 'reold {proj_idx} {tag} or\nreold {proj_idx} {greedy=True}',
                   'Reload the project {proj_idx} by running: old proj.tl_path proj.name proj.tag.\n'
                   'The argument {greedy} is optional, or specify it by True to scan more translation item,\n'
                   'which also discard less invalid lines. Default as True.'])
    table.add_row(['delete or d', 'delete {proj_idx}', 'Delete the specified project {proj_idx}.'])
    table.add_row(['clear or c', 'clear', f'Clear all projects in {default_config.project_path}.'])
    table.add_row(['translate or t', 'translate {proj_idx} {tran_api} or\ntranslate {proj_idx} {tran_api} {num_workers} or\n'
                    'translate {proj_idx} {tran_api} {num_workers} {lang}',
                     'Translate all untranslated texts using the translation API {tran_api} for the project {proj_idx}.\n'
                     'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                     'The argument {num_workers=1} is optional, or specify it to set the number of browsers to launch.  Default as 1.\n'
                     'Available translation APIs are caiyu, google, baidu, and youdao.'])
    table.add_row( ['dltranslate or dlt', 'dltranslate {proj_idx} {model_name} or\ndltranslate {proj_idx} {model_name} {lang}',
                     'Translate all untranslated texts using the AI translation model {model_name} for the project {proj_idx}.\n'
                     'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                     'Available translation models are m2m100, mbart50, and nllb200.'])
    table.add_row(['merge or m', 'merge {sproj_idx} {tproj_idx} or\nmerge {sproj_idx} {tproj_idx} {lang}',
                   'Merge translated texts from a project {sproj_idx} to the target project {tproj_idx}.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.'])
    table.add_row(['apply or a', 'apply {proj_idx} or\n apply {proj_idx} {lang} or\n'
                                 'apply {proj_idx} {lang} {greedy=True} or\n'
                                 'apply {proj_idx} {lang} {greedy=True} {skip_unmatch=True}',
                   'Apply all translated texts of project {proj_idx} to rpy files. \nThe built directory structure is the same as that of the original project.'
                   f' All rpy files will be save in {default_config.project_path}\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'The argument {greedy} is optional, or specify it by True to scan more translation item. Default as True.\n'
                   'The argument {skip_unmatch} is optional, \nor specify it by True to skip applying translated text to a new line where new_str!=old_str. Default as True.'])
    table.add_row(['revert or r', 'revert {proj_idx} or\n revert {proj_idx} {lang} or\n'
                                 'revert {proj_idx} {lang} {greedy=True}',
                   'Revert all translated texts back to untranslated ones of project {proj_idx} to rpy files. \nThis is an reverse operation of apply.\n'
                   'For arguments\' description, please refer to apply.'])
    table.add_row(['removeempty or re', 'remove_empty {proj_idx} or\n revert {proj_idx} {lang}',
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'Remove all translated lines with empty string, and move them to untranslated lines.'
                   '\nThis cmd helps you to find those translated lines with new_str=='' while old_str=='','
                   '\n and put them back to untranslated lines.'])
    table.add_row(['savehtml or sh', 'savehtml {proj_idx} or\nsavehtml {proj_idx} {lang} or\nsavehtml {proj_idx} {lang} {limit}',
                   'Save untranslated texts of project {proj_idx} to a html file,\n where Chrome (NOT recommend) or Microsoft Edge can perform translating.\n'
                   'Please use the Chrome or Microsoft Edge to translate the html file, then save to overwrite it.\n'
                   'The argument {limit} is optional, or specify it to limit the number of output lines.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'After all, use loadhtml {proj_idx} to update translated texts!'])
    table.add_row(['loadhtml or lh', 'loadhtml {proj_idx} or\nloadhtml {proj_idx} {lang} or\nloadhtml {proj_idx} {lang} {html_file}',
                   'Load translated texts from a translated html file, and apply to untranslated texts of project {proj_idx}.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'If the {html_file} is not specified, we will find the corresponding html file for the project {proj_idx} \n'
                   f'at "{default_config.project_path}/html/{{project.full_name}}.html".'])
    table.add_row(['saveexcel or se', 'saveexcel {proj_idx} or\nsaveexcel {proj_idx} {lang} or\nsaveexcel {proj_idx} {lang} {limit}',
                   'It works like savehtml, BUT save as an excel file. For augments\' description, please see savehtml.'])
    table.add_row(['loadexcel or le', 'loadexcel {proj_idx} or\nloadexcel {proj_idx} {lang} or\nloadexcel {proj_idx} {lang} {excel_file}',
                   'It works like loadhtml, BUT read from an excel file. For augments\' description, please see loadhtml.'])
    table.add_row(['dump or du', 'dump {proj_idx} or\ndump {proj_idx} {lang} or\ndump {proj_idx} {lang} {scope}',
                   'Dump all translation or untranslation (specified by argument {scope}) data of project {proj_idx} \nin language (specified by argument {lang}) to an excel file.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.\n'
                   'The argument {scope} is optional, available scopes are [trans, untrans, all].  Default as all.'])
    table.add_row(['update or up', 'update {proj_idx} or\nupdate {proj_idx} {lang} or\nupdate {proj_idx} {lang} {excel_file}',
                   'Update all translation or untranslation (specified by argument {scope}) data of project {proj_idx} \nin language (specified by argument {lang}) from an excel file.\n'
                    'It works like loadexcel, please refer to loadexcel.'])
    table.add_row(['accept or ac', 'accept {proj_idx} or accept {proj_idx} {lang}',
                   'Accept all untranslated texts as translated texts for project {proj_idx}.\n'
                   'The argument {lang} is optional, or specify it to use this language {lang}.'])
    table.add_row(['list or l', 'list or list {proj_idx}',
                   f'List projects in {default_config.project_path}, you can change it in {CONFIG_FILE}: [GLOBAL].PROJECT_PATH.\n'
                   'The argument {proj_idx} is optional, or specify it to show detailed info for the project {proj_idx}.'])
    table.add_row(['help or h', 'help', 'Show all available commands.'])
    table.add_row(['quit or q', 'quit', 'Say goodbye.'])
    print(table)


def quit_cmd():
    print('Have a nice day! Bye bye! :-)')
    sys.exit(0)


def main():
    register_cmd('help', help_cmd)
    register_cmd('h', help_cmd)
    register_cmd('quit', quit_cmd)
    register_cmd('q', quit_cmd)
    help_cmd()
    while True:
        args = my_input('What is your next step? (Enter a command (case insensitive) or Q/q to exit): ')
        args = args.strip()
        args = [c.strip() for c in args.split() if c.strip() != '']
        if len(args) >= 1:
            cmd = args[0].lower()
            if exists_cmd(cmd):
                try:
                    execute_cmd(cmd, *args[1:])
                except Exception as e:
                    print(f'error: {e}')
                    logging.exception(e)
            else:
                print(
                    f'Sorry, it seems to be an invalid command. Available commands are {all_cmds()}.')
    pass


# package cmd: pyinstaller -i imgs/proz_icon.ico -F parse_console.py --copy-metadata tqdm --copy-metadata regex --copy-metadata requests --copy-metadata packaging --copy-metadata filelock --copy-metadata numpy --copy-metadata tokenizers --copy-metadata huggingface-hub --copy-metadata safetensors --copy-metadata accelerate --copy-metadata pyyaml --copy-metadata sentencepiece
if __name__ == '__main__':
    main()

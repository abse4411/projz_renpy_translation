import logging
import os.path
import sys
import time

from config.config import default_config
from util.file import mkdir


'''
————————————————
版权声明：本文为CSDN博主「`AllureLove」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
原文链接：https://blog.csdn.net/weixin_36488653/article/details/126335142
'''
# 定义记录日志的函数
def log(log_path, level=logging.INFO,
        format="[%(asctime)s][%(filename)s:%(lineno)d, tid%(thread)d][%(levelname)s] - %(message)s ",
        datefmt="%Y-%m-%d %H:%M:%S"):
    """
    log - print log

    Args:
      log_path      - Log file path prefix.
                      Log file name will be like: PROZ_%Y-%m-%d-%H-%M-%S.log
                      Any non-exist parent directories will be created automatically
      level         - msg above the level will be displayed
                      DEBUG < INFO < WARNING < ERROR < CRITICAL
                      the default value is logging.INFO
                      default value: 'D'
      format        - format of the log
                      default format:
                      "[%(asctime)s][%(filename)s:%(lineno)d, tid%(thread)d][%(levelname)s] - %(message)s"
                      [2022-08-11 18:02:42.991][log.py:40, tid139814749787872][INFO] - HELLO WORLD
      datefmt       - format of time
                      default format: "%Y-%m-%d %H:%M:%S.%f"

    Raises:
        OSError: fail to create log directories
        IOError: fail to open log file
    """
    # 创建一个记录日志的logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # log存储地址前缀
    mkdir(log_path)
    log_file = os.path.join(log_path, time.strftime('PROZ_%Y-%m-%d-%H-%M-%S.log'))

    # 定义日志的输出格式
    formatter = logging.Formatter(format, datefmt)

    # 往文件中写日志
    # 1. 输出正常信息
    handler_info = logging.FileHandler(log_file, encoding='utf-8', delay=True)
    handler_info.setLevel(level)
    handler_info.setFormatter(formatter)
    logger.addHandler(handler_info)

    # # 2. 输出警告信息
    # handler_warning = logging.handlers.TimedRotatingFileHandler(log_path + ".log.wf", when=when, backupCount=backup,
    #                                                             encoding="utf-8")
    # handler_warning.setLevel(logging.WARNING)
    # handler_warning.setFormatter(formatter)
    # logger.addHandler(handler_warning)

    # 往控制台写日志(通过stream参数控制字体颜色)
    sh = logging.StreamHandler(stream=sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)




log(default_config.log_path)


import logging
import os.path
import time

import colorlog

# venv/Lib/site-packages/colorlog/escape_codes.py
log_colors_config = {
    'DEBUG': 'white',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}


class Logger:
    def __init__(self, trace_id=None):
        self.trace_id = trace_id

    def set_trace_id(self, trace_id):
        self.trace_id = trace_id

    def get_logger(self, name):
        if self.trace_id is not None:
            name = self.trace_id
        named_logger = logging.getLogger(name)
        # 判断是否有处理器，避免重复执行
        if not named_logger.handlers:
            # 日志输出的默认级别为warning及以上级别，设置输出info级别
            named_logger.setLevel(logging.DEBUG)
            # 创建一个处理器handler  StreamHandler()控制台实现日志输出
            sh = logging.StreamHandler()
            # 日志输出格式
            color_formatter = colorlog.ColoredFormatter(
                fmt='%(log_color)s[%(asctime)s.%(msecs)03d] %(threadName)s %(filename)s '
                    '-> %(funcName)s line:%(lineno)d '
                    '[%(levelname)s] : %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors=log_colors_config
            )
            # 创建一个格式器formatter  （日志内容：当前时间，文件，日志级别，日志描述信息）
            formatter = logging.Formatter(
                fmt="[%(asctime)s.%(msecs)03d] %(threadName)s %(filename)s "
                    "-> %(funcName)s line:%(lineno)d [%(levelname)s] : "
                    "%(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            log_dir = '../logs/{}'.format(name)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            # 创建一个文件处理器，文件写入日志
            fh = logging.FileHandler(
                filename="{}/{}_log.txt".format(log_dir, time.strftime("%Y_%m_%d", time.localtime())),
                encoding="utf8")
            # 关联控制台日志器—处理器—格式器
            named_logger.addHandler(sh)
            sh.setFormatter(color_formatter)
            # 设置处理器输出级别
            sh.setLevel(logging.DEBUG)

            # 关联文件日志器-处理器-格式器
            named_logger.addHandler(fh)
            fh.setFormatter(formatter)
            # 设置处理器输出级别
            fh.setLevel(logging.DEBUG)
        return named_logger


logger = Logger('sys')

if __name__ == '__main__':
    log = Logger().get_logger('sys')
    log.debug('debug')
    log.info('info')
    log.warning('warning')
    log.error('error')
    log.critical('critical')

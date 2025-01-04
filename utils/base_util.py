import re
import time
import traceback
from functools import wraps

import jsonpath

from utils.logging_util import logger

log = logger.get_logger('stats_time')


def file_path_format(file_path):
    return re.sub('\\\\', '/', file_path)


def to_hump(text):
    return re.sub('_([A-z])', lambda x: x[1].upper(), text)


def get_list_dim(obj, dim=0):
    if isinstance(obj, list):
        dim = dim + 1
        if isinstance(obj[0], list):
            dim = get_list_dim(obj[0], dim)
    return dim


def stats_time(name):
    def c(func):
        @wraps(func)
        def b(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            log.info("{} 执行时间：{}".format(name, end - start))
            return result

        return b

    return c


def retry(retry_param_path: str, suc_func: callable):
    """
    函数重试
    :param retry_param_path: 重试参数的获取路径，从函数的输入参数获取，比如：$[1].retry
    :param suc_func: 根据返回结果判断是否执行成功
    :return: 函数的结果
    """

    def c(func):
        @wraps(func)
        def b(*args, **kwargs):
            retry_param = jsonpath.jsonpath(list(args), retry_param_path)
            if not retry_param or not isinstance(retry_param, list) or len(retry_param[0]) < 3:
                return func(*args, **kwargs)
            delay, interval, expire = retry_param[0]
            log.debug("等待异步执行结果 delay:{}s, interval:{}s, expire:{}s".format(delay, interval, expire))
            time.sleep(delay)
            elapsed = delay
            result = None
            while elapsed < expire:
                log.debug("等待异步执行结果 elapsed:{}s".format(elapsed))
                try:
                    result = func(*args, **kwargs)
                    if suc_func(result):
                        break
                except Exception as e:
                    traceback.print_exc()
                    log.info(e)
                time.sleep(interval)
                elapsed = elapsed + interval
            return result

        return b

    return c


def batch_split(lens: int, batch_size: int) -> [(int, int)]:
    start, end = 0, 0
    batch_indexes = []
    while start < lens:
        end = start + batch_size - 1
        if end > lens:
            end = lens - 1
        batch_indexes.append((start, end))
        start = end + 1
    return batch_indexes


if __name__ == '__main__':
    l1 = ['a']
    l2 = ['b']
    d = zip(l1, l2)
    print(dict(d))
    print(['float32'] * 3)

import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from context import Request
from simulate_request.field_config import RequestStats, URL, RESULT_STATS_FUNC, PARAM_PACK, PARAM_PACK_FIELD
from utils.dict_util import dict_set
from utils.logging_util import logger
from utils.request_util import request_post

log = logger.get_logger('request_executor')


class ResultStats:
    def __init__(self):
        self.response_statics: list[RequestStats] = []
        self.total_num = 0
        self.success_num = 0
        self.fail_num = 0
        self.fail_records = []

    def stats(self):
        for stats in self.response_statics:
            self.total_num = self.total_num + stats.total_num
            self.success_num = self.success_num + stats.success_num
            self.fail_num = self.fail_num + stats.fail_num
            self.fail_records.extend(stats.fail_records)
        log.info('totalNum:{}, success_num:{}, fail_num:{}, \nfail_records:{}'.format(self.total_num, self.success_num,
                                                                                      self.fail_num,
                                                                                      self.fail_records))


class RequestExecutor:

    def __init__(self, request_context):
        """
        执行url请求
        :param request_context: http请求的上下文
        """
        assert isinstance(request_context, Request)
        self.request_context = request_context
        self.result_stats = ResultStats()

    def execute(self, request_name, request_params, request_config, test=False):
        # document why this method is empty
        pass

    def stats_result(self, param, result, result_stats_func):
        if result_stats_func is None:
            def f(p, r):
                stats = RequestStats()
                stats.total_num = len(p)
                stats.success_num = len(r)
                return stats

            result_stats_func = f
        assert callable(result_stats_func)
        s = result_stats_func(param, result)
        self.result_stats.response_statics.append(s)


class CurlRequestExecutor(RequestExecutor):
    CURL_PREFIX = 'curl -H \"Content-Type: application/json\" -X POST -d \''

    def execute(self, request_name, request_params, request_config, test=False):
        for request_param in request_params:
            request_param = put_param_in_pack(request_config, request_param)
            url = self.request_context.domain + request_config[URL]
            curl = self.CURL_PREFIX + json.dumps(request_param) + '\' \"' + url + '\"'
            log.info(curl)


class RemoteRequestExecutor(RequestExecutor):
    thread_nums = 1
    headers = None

    def set_thread_nums(self, thread_nums):
        if not isinstance(thread_nums, int):
            thread_nums = 1
        if thread_nums <= 0:
            thread_nums = 1
        self.thread_nums = thread_nums

    def set_headers(self, headers=None):
        self.headers = headers

    def execute(self, request_name, request_params, request_config, test=False):
        url = self.request_context.domain + request_config[URL]
        request_params_ = []
        for param in request_params:
            request_params_.append(put_param_in_pack(request_config, param))
        if test:
            log.warn('it is testing,do not request http. url:{}'.format(url))
            for p in request_params_:
                log.info('request_param:{}'.format(p))
            return
        result_stats_func = request_config[RESULT_STATS_FUNC] if RESULT_STATS_FUNC in request_config else None
        if self.thread_nums > 1:
            log.info("启用多线程执行，thread_nums：{}".format(self.thread_nums))
            url_param = [(url, param, self.headers) for param in request_params_]
            with ThreadPoolExecutor(max_workers=self.thread_nums) as executor:
                for result in executor.map(lambda params: request_post(*params), url_param):
                    self.stats_result(url_param, result, result_stats_func)
                    log.info("request_post result: {}".format(result))
        else:
            for request_param in request_params_:
                result = request_post(url, request_param, self.headers)
                self.stats_result(request_param, result, result_stats_func)
                log.info("request_post result: {}".format(result))
        self.result_stats.stats()


def put_param_in_pack(request_config, request_param):
    param_pack = request_config.get(PARAM_PACK)
    param_pack_field = request_config.get(PARAM_PACK_FIELD)
    param_pack_copy = deepcopy(param_pack)
    if param_pack_copy is not None and param_pack_field is not None:
        _value = {param_pack_field: request_param}
        dict_set(param_pack_copy, param_pack_field, _value)
        request_param = param_pack_copy
    return request_param

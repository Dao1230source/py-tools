import json
import re
from concurrent.futures import ThreadPoolExecutor

import jsonpath

from utils.base_util import stats_time, retry
from utils.logging_util import logger
from utils.mysql_util import get_conn_from_context, select_dict_res_from_db, execute_other_sql
from utils.request_util import request_post

logger.set_trace_id('auto_test')
log = logger.get_logger('auto_test')

# 自动测试之前的准备工作
BEFORE = 'before'
# 自动测试
TEST = 'test'
# 测试之后的工作
AFTER = 'after'
# 结果检验
NODE_PREDICATE = 'predicate'
# 节点是否需要重试
NODE_PREDICATE_RETRY = 'retry'
# 节点的输入参数
NODE_INPUTS = 'inputs'
# 异步执行, 只有http请求才会有异步执行
NODE_ASYNC = 'async'
# 是否是判断节点
NODE_IF = 'if'
NODE_IF_TRUE = 'true'
NODE_IF_FALSE = 'false'
# 节点的描述
NODE_DESC = 'desc'
# 节点的标记，用于控制整个流程的开始节点和结束节点
NODE_TAG = 'tag'
'''
操作数据库
'''
# select返回dict类型的结果，非select返回影响行数
NODE_SQL = 'sql'
# 是否执行executemany方法
DATABASE_TYPE_PARAM_MANY = 'many'
'''
调用接口
'''
NODE_URL = 'url'
'''
自定义函数
'''
NODE_FUNC = 'func'


class AutoTest:
    def __init__(self, execute_context):
        self.context = execute_context
        log.info('database:{}'.format(self.context.database))
        self.conn = get_conn_from_context(database=self.context.database)

    @staticmethod
    def execute_func(func_ref, extra_funcs):
        """
        执行额外的函数
        :param func_ref:
        :param extra_funcs:
        {
            tag1: func1,
            tag2: func2
        }
        :return:
        """
        if isinstance(func_ref, str) and extra_funcs is not None and func_ref in extra_funcs:
            func = extra_funcs[func_ref]
            if callable(func):
                func()

    @staticmethod
    def parse_predicate(predicate, target_dict):
        """
        解析断言表达式
        eg: $.cnt == 0 使用 jsonpath 从target_dict中获取cnt值与 0 比较

        json.load()从json文件中读取数据
        json.loads()将str类型的数据转换为dict类型
        json.dumps()将dict类型的数据转成str
        json.dump()将数据以json的数据类型写入文件中

        jsonpath用法：
        $.store.book[*].author	书点所有书的作者
        $..author	            所有的作者
        $.store.*	            store的所有元素。
        $.store..price	        store里面所有东西的price
        $..book[2]	            第三个书
        $..book[(@.length-1)]	最后一本书
        $..book[0,1]	        前面的两本书。
        $..book[:2]
        $..book[?(@.isbn)]	    过滤出所有的包含isbn的书。
        $..book[?(@.price<10)]	过滤出价格低于10的书。
        $..*	                所有元素。

        :param predicate:
        :param target_dict:
        :return: 解析后的表达式
        """
        paths = re.findall(r'\$[\w\\.*@?()\[\]]+', predicate)
        for _path in paths:
            val = jsonpath.jsonpath(target_dict, _path)[0]
            predicate = predicate.replace(_path, str(val))
        return predicate

    @stats_time("auto_test")
    def execute(self, file_path: str, start_node: str = None, end_node: str = None, **kwargs):
        """
        入口
        :param file_path: json路径
        :param start_node: 开始节点
        :param end_node: 结束节点
        :param kwargs: 额外执行的函数，
        extra_funcs={
            tag1: func1,
            tag2: func2,
        }
        """
        log.info('execute case: {}'.format(file_path))
        with open(file_path, encoding='UTF-8') as f:
            json_data = json.load(f)
            log.info(json_data[NODE_DESC])
            stages = [BEFORE, TEST, AFTER]
            extra_funcs = kwargs['extra_funcs'] if 'extra_funcs' in kwargs else None
            for s in stages:
                self.execute_nodes(json_data.get(s), start_node, end_node, extra_funcs)

    def assert_predicate(self, predicate, target_dict, extra_funcs=None):
        predicate_result = True
        if isinstance(predicate, str):
            predicate_parsed = AutoTest.parse_predicate(predicate, target_dict)
            predicate_result = eval(predicate_parsed)
            log.info("判定条件:{}, 解析之后：{}, 结果：{}".format(predicate, predicate_parsed, predicate_result))
        elif isinstance(predicate, dict):
            predicate_result, _ = self.execute_node(predicate, extra_funcs=extra_funcs)
        elif isinstance(predicate, list):
            for i in predicate:
                if not self.assert_predicate(i, target_dict, extra_funcs=extra_funcs):
                    return False
        return predicate_result

    def execute_nodes(self, node_list, start_node=None, end_node=None, extra_funcs=None):
        if node_list is None or not isinstance(node_list, list):
            return
        for node in node_list:
            res, flag = self.execute_node(node, start_node, end_node, extra_funcs)
            assert (res is True)
            if flag == 'start':
                start_node = None
            if flag == 'end':
                break

    @retry(retry_param_path='$[1].retry', suc_func=lambda x: x[0])
    def execute_node(self, node_data, start=None, end=None, extra_funcs=None):
        """
        执行节点
        :param node_data:  节点数据
        :param start: 流程从该节点开始执行
        :param end: 流程执行该节点后结束执行，
        :param extra_funcs: 流程执行该节点后结束执行，
        :return: predicate_result：执行之后判断结果，node_flag：start：开始节点；end：终止节点；'skip'：默认跳过改节点
        """
        flag = 'skip'
        if start is not None:
            if NODE_TAG not in node_data or node_data[NODE_TAG] != start:
                log.info("跳过执行该节点：{}".format(node_data.get(NODE_DESC)))
                return True, flag
        flag = 'start'
        res = None
        if NODE_IF in node_data:
            if self.execute_node(node_data[NODE_IF], start, end, extra_funcs):
                return AutoTest.execute_node(node_data[NODE_IF_TRUE], start, end, extra_funcs)
            else:
                return AutoTest.execute_node(node_data[NODE_IF_FALSE], start, end, extra_funcs)
        inputs = None
        if NODE_INPUTS in node_data:
            inputs = node_data[NODE_INPUTS]
        log.info("desc:{}, inputs：{}".format(node_data.get(NODE_DESC), inputs))
        if NODE_SQL in node_data:
            sql = node_data[NODE_SQL]
            log.debug('sql:{}'.format(sql))
            sql_con = get_conn_from_context(conn=self.conn, database=self.context.database)
            sql_cursor = sql_con.cursor()
            if sql.startswith('select'):
                res = select_dict_res_from_db(sql_con, sql_cursor, sql, inputs)[0]
            else:
                is_many = DATABASE_TYPE_PARAM_MANY in node_data and node_data[DATABASE_TYPE_PARAM_MANY]
                res = execute_other_sql(sql_con, sql_cursor, sql, inputs, is_many)
                log.debug("{} row affected".format(res))
        elif NODE_URL in node_data:
            url = self.context.request.domain + node_data[NODE_URL]
            if NODE_ASYNC in node_data and isinstance(inputs, list):
                param = [(url, json_params) for json_params in inputs]
                with ThreadPoolExecutor(max_workers=10) as executor:
                    for result in executor.map(lambda p: request_post(*p), param):
                        log.debug("request_post result: {}".format(result))
                res = 'async'
            else:
                res = request_post(url, inputs)
        elif NODE_FUNC in node_data:
            AutoTest.execute_func(node_data[NODE_FUNC], extra_funcs)
        else:
            log.debug('可执行模块中没有database或request部分,请检查是否配置完全')
        predicate_result = True
        if NODE_PREDICATE in node_data:
            predicate_result = self.assert_predicate(node_data[NODE_PREDICATE], res, extra_funcs=extra_funcs)
        if end is not None:
            if NODE_TAG in node_data and node_data[NODE_TAG] == end:
                log.info("从此节点结束整个流程，{}".format(node_data.get(NODE_DESC)))
                flag = 'end'
                return predicate_result, flag
        return predicate_result, flag

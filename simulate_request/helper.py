from simulate_request.data_parser import DataParser
from simulate_request.data_source import DataSource
from simulate_request.request_executor import RequestExecutor, RemoteRequestExecutor
from utils.logging_util import logger

log = logger.get_logger('simulate_request_helper')

"""
使用isinstance()判断时，class的类型是根据import路径来的，
例如 DataParser
如下import
    from simulate_request.data_parser import DataParser
    class：simulate_request.data_parser.DataParser
如下import
    from data_parser import DataParser
    class：data_parser.DataParser
如果import路径不同，isinstance就会返回false
所以最好按相对项目的目录import
"""


class SimulateRequest:
    global_context = None
    data_source = None
    data_parser = None
    request_executor = None

    def __init__(self, global_context):
        self.global_context = global_context

    def set_data_source(self, data_source):
        assert isinstance(data_source, DataSource)
        self.data_source = data_source

    def set_data_parser(self, data_parser):
        assert isinstance(data_parser, DataParser)
        self.data_parser = data_parser

    def set_request_executor(self, request_executor):
        assert isinstance(request_executor, RequestExecutor)
        self.request_executor = request_executor

    def set_thread_nums(self, thread_nums):
        if isinstance(self.request_executor, RemoteRequestExecutor):
            self.request_executor.set_thread_nums(thread_nums)

    def set_headers(self, headers):
        if isinstance(self.request_executor, RemoteRequestExecutor):
            self.request_executor.set_headers(headers)

    def set_batch_size(self, batch_size):
        self.data_parser.set_batch_size(batch_size)

    def set_extra_funcs(self, extra_funcs):
        self.data_parser.set_extra_funcs(extra_funcs)

    def execute(self, test=False):
        data = self.data_source.get_data()
        request_params, request_config = self.data_parser.parser(data)
        self.request_executor.execute(self.data_parser.request_name, request_params, request_config, test)

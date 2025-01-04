import json
import re
from copy import deepcopy

import pandas as pd

from simulate_request.field_config import config_json, data_update_field, \
    IS_BATCH, MAX_SIZE, GROUP_FIELDS, FIELD_MAP, PRIMARY_KEYS
from utils.logging_util import logger

log = logger.get_logger('data_parser')


class DataParser:
    batch_size = 100
    extra_funcs = None

    def __init__(self, request_name):
        self.request_name = request_name

    def set_batch_size(self, batch_size):
        if not isinstance(batch_size, int):
            batch_size = 100
        if batch_size <= 0:
            batch_size = 100
        self.batch_size = batch_size

    def set_extra_funcs(self, extra_funcs):
        assert isinstance(extra_funcs, dict)
        self.extra_funcs = extra_funcs

    def parser(self, data):
        config = config_json()
        request_config = deepcopy(config[self.request_name])
        is_batch = request_config[IS_BATCH]
        size = self.batch_size if is_batch else 1
        # 不可超过设置的最大批量数
        if MAX_SIZE in request_config and size > request_config[MAX_SIZE]:
            size = request_config[MAX_SIZE]
            log.debug("设置的最大批量数：{}".format(request_config[MAX_SIZE]))
        # 某些请求参数必须按字段分组
        group_fields = request_config.get(GROUP_FIELDS)
        request_fields = request_config[FIELD_MAP]
        data, fields = prepare_df(data, request_fields, self.extra_funcs)
        primary_keys = [i.name for i in request_config[PRIMARY_KEYS]] if PRIMARY_KEYS in request_config else []
        assembled_json_list = assemble_param_from_df(data=data, request_fields=fields, primary_keys=primary_keys,
                                                     batch_size=size, is_batch=is_batch, group_fields=group_fields)
        return assembled_json_list, request_config


def assemble_param_from_df(data, request_fields, primary_keys, is_batch=True, batch_size=100, group_fields=None):
    """
    从 DataFrame数据源 中获取数据组装成请求参数
    :param primary_keys:
    :param is_batch:
    :param group_fields: 分组字段['field_name']，同一分组的记录分配在同一批次
    :param data: DataFrame格式数据源
    :param request_fields: 请求字段
    :param batch_size: 批次大小
    :return:
    """
    param_json_list = []
    # 去重
    if primary_keys is not None and len(primary_keys) > 0:
        data.drop_duplicates(subset=primary_keys, keep='first', inplace=True)
    lens = data.shape[0]
    data.reset_index(drop=True, inplace=True)
    start, end = 0, 0
    batch_indexes = []
    # 如果有分组的要求
    if group_fields is not None:
        grouped = pd.DataFrame(columns=data.columns)
        for v, group in data.groupby(group_fields):
            grouped = pd.concat([grouped, group], ignore_index=True)
            end = end + len(group)
            if end - start >= batch_size:
                batch_indexes.append((start, end - 1))
                start = end
        if end > start:
            batch_indexes.append((start, end - 1))
        grouped.reset_index(drop=True, inplace=True)
        print("数据需按 {} 分组处理，分组索引：{}".format(group_fields, batch_indexes))
    else:
        while start < lens:
            end = start + batch_size - 1
            if end > lens:
                end = lens
            batch_indexes.append((start, end))
            start = end + 1
    for idx in batch_indexes:
        start, end = idx
        request_fields_ = []
        for i in request_fields:
            if i in data.columns:
                request_fields_.append(i)
        subsection = data.loc[start:end, request_fields_]
        json_str = subsection.to_json(orient='index')
        json_str = re.sub(r'"\d+":', '', json_str)
        json_str = json_str[1:-1]
        if is_batch:
            json_str = '[{}]'.format(json_str)
        param_json_list.append(json.loads(json_str))
    return param_json_list


def prepare_df(data, request_fields, extra_funcs=None):
    for field in request_fields:
        if extra_funcs is not None and field.name in extra_funcs:
            extra_funcs[field.name](field)
        data_update_field(data, field)
    fields = [i.name for i in request_fields]
    return data, fields

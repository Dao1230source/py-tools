import os

import openpyxl
import pandas as pd
from pandas import DataFrame

from utils.base_util import file_path_format


def get_df_from_excel(file_path, sheet_name='Sheet0', converters=None):
    if converters is None:
        converters = {}
    file_path = file_path_format(file_path)
    return pd.read_excel(file_path, engine='openpyxl', sheet_name=sheet_name, converters=converters)


def save_as(file_path, new_file_path=None):
    df = get_df_from_excel(file_path)
    writer = pd.ExcelWriter(file_path, engine='openpyxl', sheet_name='Sheet0')
    if file_path is None:
        new_file_path = file_path
    writer_new = pd.ExcelWriter(new_file_path, engine='openpyxl')
    book = openpyxl.load_workbook(writer.path)
    writer_new.book = book
    df.to_excel(writer_new, 'Sheet0', index=False)
    writer.close()
    writer_new.save()
    writer_new.close()


def new_df(inputs):
    if isinstance(inputs, dict):
        return pd.DataFrame.from_dict(inputs, orient='index').T
    return pd.DataFrame.from_dict(inputs, orient='columns')


def dim_list_to_df(dim_list, column_name):
    df = pd.DataFrame(dim_list)
    df.columns = column_name
    return df


def get_list_data_from_df(df, column_names, clear_all=False):
    records = []
    record_ids = []
    for row in df.itertuples():
        if pd.isna(getattr(row, 'sku_no')):
            break
        row_data = list()
        for column_name in column_names:
            data = getattr(row, column_name)
            if pd.isna(data):
                data = None
            row_data.append(data)
        records.append(row_data)
        if clear_all:
            if len(record_ids) > 0:
                continue
            unique_key_column_names = ['warehouse_code', 'sku_no', 'inventory_status', 'company_code']
            unique_key_data = []
            for column_name in unique_key_column_names:
                data = getattr(row, column_name)
                if pd.isna(data):
                    data = None
                unique_key_data.append(data)
            record_ids.append(unique_key_data)
        else:
            record_ids = [i[0] for i in records]
    return records, record_ids


def row_one_to_multi(df: DataFrame, column_name, split_str: str):
    """
    一行转多行
    :param df: DataFrame
    :param column_name: 列名
    :param split_str: 分隔字符
    :return: df
    """
    # 拆分为多列
    df_temp = df[column_name].str.split(split_str, expand=True)
    # 行转列
    df_temp = df_temp.stack()
    # 重置索引，删除多余索引
    df_temp = df_temp.reset_index(level=1, drop=True)
    # 数据合并
    df_temp.db_profile_name = column_name
    return df.drop([column_name], axis=1).join(df_temp).reset_index().drop(columns='index')


class DataAndSheet:
    def __init__(self, data: pd.DataFrame, sheet_name: str):
        self.data = data
        self.sheet_name = sheet_name

    def get_data(self):
        return self.data

    def get_sheet_name(self):
        return self.sheet_name


def save_as_excel(sheet_of_data: [DataAndSheet], file_path: str) -> None:
    """
    保存到 excel
    :param sheet_of_data: SheetOfData
    :param file_path: file_path
    :return: None
    """
    if os.path.exists(file_path):
        os.remove(file_path)
    writer = pd.ExcelWriter(file_path, engine='openpyxl')
    for sd in sheet_of_data:
        if sd.get_data() is not None:
            sd.get_data().to_excel(writer, sd.get_sheet_name(), index=False)
    writer.close()


class Group:
    def __init__(self, data: pd.DataFrame, by_columns: [str], group_columns: [str],
                 pre_handler: (str, callable) = None):
        """
        对数据进行分组统计
        :param data:
        :param by_columns:
        :param group_columns:
        :param pre_handler: 数据预处理
        (字段名称，对该字段数据进行处理的函数)
        """
        self.data = data
        self.by_columns = by_columns
        self.group_columns = group_columns
        if pre_handler is not None:
            column_name, handler = pre_handler
            data[column_name] = data[column_name].apply(handler)
        group_data = data[by_columns + group_columns]
        self.group_data = group_data.astype(dict(zip(group_columns, ['float32'] * len(group_columns))))

    @staticmethod
    def mean(group):
        mean_data = group.group_data.groupby(group.by_columns).mean()
        return mean_data.rename(columns=dict(zip(group.group_columns, ['mean_' + c for c in group.group_columns])))

    @staticmethod
    def sum(group):
        data_ = group.group_data.groupby(group.by_columns).sum()
        return data_.rename(columns=dict(zip(group.group_columns, ['sum_' + c for c in group.group_columns])))

    @staticmethod
    def count(group):
        data_ = group.group_data.groupby(group.by_columns).count()
        return data_.rename(columns=dict(zip(group.group_columns, ['count_' + c for c in group.group_columns])))

    @staticmethod
    def min(group):
        data_ = group.group_data.groupby(group.by_columns).min()
        return data_.rename(columns=dict(zip(group.group_columns, ['min_' + c for c in group.group_columns])))

    @staticmethod
    def max(group):
        data_ = group.group_data.groupby(group.by_columns).max()
        return data_.rename(columns=dict(zip(group.group_columns, ['max_' + c for c in group.group_columns])))


def group_by(data: pd.DataFrame, by_columns: [str], group_columns: [str],
             actions=None, pre_handler: (str, callable) = None):
    if actions is None:
        actions = [Group.mean, Group.sum, Group.count, Group.min, Group.max]
    group = Group(data, by_columns, group_columns, pre_handler)
    action_datas = []
    for a in actions:
        action_datas.append(a(group))
    s_data_stats = pd.concat(action_datas, axis=1)
    return s_data_stats.reset_index()


def row_concat(datas: [pd.DataFrame]) -> pd.DataFrame:
    concat_data = pd.concat(datas, axis=0, ignore_index=True)
    return concat_data.reset_index()

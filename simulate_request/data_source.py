from context.context import Database
from utils.df_util import get_df_from_excel, new_df, dim_list_to_df
from utils.logging_util import logger
from utils.mysql_util import get_conn_from_context, get_list_of_list_from_query, get_field_list

log = logger.get_logger('data_source')


def get_df_from_db(query_sql, database):
    conn = get_conn_from_context(database=database)
    cursor = conn.cursor()
    cursor.execute(query_sql)
    list_of_list_result = get_list_of_list_from_query(cursor)
    log.debug("执行结果：{}".format(len(list_of_list_result)))
    field_list = get_field_list(cursor)
    return dim_list_to_df(list_of_list_result, field_list)


class DataSource:
    def __init__(self):
        self.source = None

    def get_data(self):
        pass


class FileDataSource(DataSource):
    def __init__(self, file_path, sheet_name, converters=None):
        super().__init__()
        self.file_path = file_path
        self.sheet_name = sheet_name
        self.converters = converters

    def get_data(self):
        return get_df_from_excel(file_path=self.file_path, sheet_name=self.sheet_name, converters=self.converters)


class SqlDataSource(DataSource):
    def __init__(self, sql_query, database_context):
        super().__init__()
        self.sql_query = sql_query
        assert isinstance(database_context, Database)
        self.db_context = database_context

    def get_data(self):
        return get_df_from_db(self.sql_query, self.db_context)


class InputDataSource(DataSource):
    def __init__(self, input_data):
        super().__init__()
        self.input_data = input_data

    def get_data(self):
        return new_df(inputs=self.input_data)


if __name__ == '__main__':
    input_data_source = InputDataSource(input_data=[])
    assert isinstance(input_data_source, DataSource)

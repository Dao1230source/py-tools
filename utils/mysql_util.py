import oracledb
import pymysql
from pymysql import Connection

from context import Database


def get_conn(host, port, user, password, database, conn=None) -> Connection:
    if conn is None:
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
    try:
        conn.ping(True)
    except Exception as e:
        print('重新获取数据库连接:{}'.format(e))
        conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
    return conn


def conn_oracle(user="MRM", password="mrmdev#123", dsn="10.207.8.164:1521/epsedev"):
    oracledb.init_oracle_client(
        lib_dir=r'G:\01404679\program\instantclient-basiclite-windows.x64-21.9.0.0.0dbru\instantclient_21_9')
    # Connect as user "hr" with password "welcome" to the "orclpdb1" service running on this computer.
    return oracledb.connect(user=user, password=password, dsn=dsn)


def get_conn_from_context(database: Database, conn=None) -> Connection:
    return get_conn(database.host, database.port, database.user, database.password, database.db, conn=conn)


def get_field_list(cursor):
    return [desc[0] for desc in cursor.description]


def get_list_of_list_from_query(cursor):
    return [list(i) for i in cursor.fetchall()]


def get_field_index_dict(cursor):
    field_index_dict = dict()
    index = 0
    for desc in cursor.description:
        field_index_dict[desc[0]] = index
        index = index + 1
    return field_index_dict


def res_to_dict(rows, field_index_dict):
    res_dict_list = list()
    for row in rows:
        row_dict = dict()
        for field, index in field_index_dict.items():
            row_dict[field] = row[index]
        res_dict_list.append(row_dict)
    return res_dict_list


def execute_sql(conn, cursor, sql, inputs=None, is_many=False):
    if is_many:
        cursor.executemany(sql, inputs)
    else:
        cursor.execute(sql, inputs)
    return conn, cursor


def select_dict_res_from_db(conn, cursor, query_sql, inputs=None):
    conn, cursor = execute_sql(conn, cursor, query_sql, inputs, False)
    field_index_dict = get_field_index_dict(cursor)
    return res_to_dict(cursor.fetchall(), field_index_dict)


def execute_other_sql(conn, cursor, sql, inputs=None, is_many=False):
    conn, cursor = execute_sql(conn, cursor, sql, inputs, is_many)
    conn.commit()
    return cursor.rowcount

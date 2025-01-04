from context.context import Context, Environment, Local, Dev, Sit, Prod


class EnvIms(Environment):
    db_host: str = 'opcims-m.dbsit.sfcloud.local'
    db_user: str = 'opcims'
    db_password: str = 'opcims@123456'
    db_database: str = 'opcims'
    request_domain: str = 'http://localhost:8080/'


class EnvLocalIms(Local, EnvIms):
    db_database: str = 'test'
    request_domain: str = 'http://localhost:8080/inventory/manage/inner/'


class EnvDevIms(Dev, EnvIms):
    pass


class EnvSitIms(Sit, EnvIms):
    request_domain: str = 'http://opc-ims.sit.sf-express.com:80/'


class EnvProdIms(Prod, EnvIms):
    request_domain: str = 'http://opc-ims.sf-express.com:80/'


class ContextIms(Context):
    def __init__(self):
        super(ContextIms, self).__init__(EnvLocalIms(), EnvDevIms(), EnvSitIms(), EnvProdIms())


if __name__ == '__main__':
    """
    这里管理所有数据库和http请求相关的配置项
    """
    context = ContextIms()
    print(context.db_use_local().database.db)

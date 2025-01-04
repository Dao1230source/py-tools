from context.context import Context, Environment, Local, Dev, Sit, Prod


class EnvEwms(Environment):
    db_host: str = 'ewmsorder-m.dbsit.sfcloud.local'
    db_user: str = 'ewmsorder'
    db_password: str = 'Java1234$'
    db_database: str = 'ewmsorder'
    request_domain: str = 'http://localhost:8090/'


class EnvLocalEwms(Local, EnvEwms):
    pass


class EnvDevEwms(Dev, EnvEwms):
    pass


class EnvSitEwms(Sit, EnvEwms):
    request_domain: str = 'http://opc-node.sit.sf-express.com/'


class EnvProdEwms(Prod, EnvEwms):
    request_domain: str = 'https://ewms-gw.sf-express.com/'


class ContextEwms(Context):
    def __init__(self):
        super(ContextEwms, self).__init__(EnvLocalEwms(), EnvDevEwms(), EnvSitEwms(), EnvProdEwms())

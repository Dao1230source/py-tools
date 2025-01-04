from context.context import Context, Environment, Local, Dev, Sit, Prod


class EnvMscpExtData(Environment):
    db_host: str = 'extdatasource-m.dbsit.sfcloud.local'
    db_user: str = 'extdatasource'
    db_password: str = 'Mscp@211314'
    db_database: str = 'extdatasource'
    request_domain: str = 'http://localhost:8080/'


class EnvLocalMscpExtDataExtData(Local, EnvMscpExtData):
    request_domain: str = 'https://http://localhost:7030/external-datasource-provider'


class EnvDevMscpExtDataExtData(Dev, EnvMscpExtData):
    db_host = "extds2dev-m.dbsit.sfcloud.local"
    request_domain: str = 'https://mscp-gw-dev.sit.sf-express.com:80/ext-data'


class EnvSitMscpExtDataExtData(Sit, EnvMscpExtData):
    request_domain: str = 'https://mscp-gw.intsit.sfcloud.local:1080/ext-data'


class EnvProdMscpExtDataExtData(Prod, EnvMscpExtData):
    request_domain: str = 'https://mscp-gw.int.sfcloud.local:1080/ext-data'


class ContextMscpExtData(Context):
    def __init__(self):
        super(ContextMscpExtData, self).__init__(EnvLocalMscpExtDataExtData(), EnvDevMscpExtDataExtData(),
                                                 EnvSitMscpExtDataExtData(),
                                                 EnvProdMscpExtDataExtData())


class EnvMscpOM(Environment):
    db_host: str = 'opmgmt2dev-m.dbsit.sfcloud.local'
    db_user: str = 'opmanagement'
    db_password: str = 'Mscp@211314'
    db_database: str = 'opmanagement'
    request_domain: str = 'http://localhost:7010/operation-management-provider/'


class EnvLocalMscpOM(Local, EnvMscpOM):
    request_domain: str = 'http://localhost:7010/operation-management-provider/'


class EnvDevMscpOM(Dev, EnvMscpOM):
    request_domain: str = 'http://localhost:8080/operation-management-provider/'


class EnvSitMscpOM(Sit, EnvMscpOM):
    db_host: str = 'opmanagement-m.dbsit.sfcloud.local'
    request_domain: str = 'http://mscp-gw.intsit.sfcloud.local:1080/om/'


class EnvProdMscpOM(Prod, EnvMscpOM):
    request_domain: str = 'https://mscp-om.sf-express.com/api/om/'


class ContextMscpOM(Context):
    def __init__(self):
        super(ContextMscpOM, self).__init__(EnvLocalMscpOM(), EnvDevMscpOM(), EnvSitMscpOM(), EnvProdMscpOM())


class EnvMscpSS(Environment):
    db_host: str = 'sysservice2dev-m.dbsit.sfcloud.local'
    db_user: str = 'systemservice'
    db_password: str = 'Mscp@211314'
    db_database: str = 'systemservice'
    request_domain: str = 'http://localhost:7010/system-service-provider'


class EnvLocalMscpSS(Local, EnvMscpSS):
    pass


class EnvDevMscpSS(Dev, EnvMscpSS):
    request_domain: str = 'https://mscp-gw-dev.sit.sf-express.com:80/ss'


class EnvSitMscpSS(Sit, EnvMscpSS):
    db_host: str = 'systemservice-m.dbsit.sfcloud.local'
    db_password: str = 'mscp@211314'
    request_domain: str = 'https://mscp-gw.intsit.sfcloud.local:1080/ss'


class EnvProdMscpSS(Prod, EnvMscpSS):
    request_domain: str = 'https://mscp-gw.int.sfcloud.local:1080/ss'


class ContextMscpSS(Context):
    def __init__(self):
        super(ContextMscpSS, self).__init__(EnvLocalMscpSS(), EnvDevMscpSS(), EnvSitMscpSS(), EnvProdMscpSS())

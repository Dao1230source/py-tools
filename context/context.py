class Database:
    def __init__(self, host, port, user, password, db):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db


class Request:
    def __init__(self, domain):
        """
        request
        :param domain: 域名
        """
        self.domain = domain


class Environment:
    db_profile_name: str = 'environment'
    db_host: str = None
    db_port: int = 3306
    db_user: str = None
    db_password: str = None
    db_database: str = None
    request_profile_name = 'environment'
    request_domain: str = None

    def __init__(self):
        self.database = Database(self.db_host, self.db_port, self.db_user, self.db_password, self.db_database)
        self.request = Request(self.request_domain)


class Local(Environment):
    db_profile_name = 'local'
    request_profile_name = 'local'
    pass


class Dev(Environment):
    db_profile_name = 'dev'
    request_profile_name = 'dev'
    pass


class Sit(Environment):
    db_profile_name = 'sit'
    request_profile_name = 'sit'
    pass


class Prod(Environment):
    db_profile_name = 'prod'
    request_profile_name = 'prod'
    pass


class Context:
    db_profile_name = 'prod'
    request_profile_name = 'prod'

    def __init__(self, local: Local, dev: Dev, sit: Sit, prod: Prod):
        self.local = local
        self.dev = dev
        self.sit = sit
        self.prod = prod
        self.database = local.database
        self.request = local.request

    def db_use_local(self):
        self.database = self.local.database
        self.db_profile_name = self.local.db_profile_name
        return self

    def db_use_dev(self):
        self.database = self.dev.database
        self.db_profile_name = self.dev.db_profile_name
        return self

    def db_use_sit(self):
        self.database = self.sit.database
        self.db_profile_name = self.sit.db_profile_name
        return self

    def db_use_prod(self):
        self.database = self.prod.database
        self.db_profile_name = self.prod.db_profile_name
        return self

    def request_use_local(self):
        self.request = self.local.request
        self.request_profile_name = self.local.db_profile_name
        return self

    def request_use_dev(self):
        self.request = self.dev.request
        self.request_profile_name = self.dev.db_profile_name
        return self

    def request_use_sit(self):
        self.request = self.sit.request
        self.request_profile_name = self.sit.request_profile_name
        return self

    def request_use_prod(self):
        self.request = self.prod.request
        self.request_profile_name = self.prod.request_profile_name
        return self

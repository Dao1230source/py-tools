from context.context import Context, Environment, Local, Dev, Sit, Prod


class EnvOpcWeb(Environment):
    request_domain: str = 'http://opc-node.sit.sf-express.com/'


class EnvLocalOpcWeb(Local, EnvOpcWeb):
    pass


class EnvDevOpcWeb(Dev, EnvOpcWeb):
    pass


class EnvSitOpcWeb(Sit, EnvOpcWeb):
    request_domain: str = 'http://opc-node.sit.sf-express.com/'


class EnvProdOpcWeb(Prod, EnvOpcWeb):
    request_domain: str = 'http://opc-node.sf-express.com/'


class ContextOpcWeb(Context):
    def __init__(self):
        super(ContextOpcWeb, self).__init__(EnvLocalOpcWeb(), EnvDevOpcWeb(), EnvSitOpcWeb(), EnvProdOpcWeb())

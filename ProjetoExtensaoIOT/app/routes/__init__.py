from app.routes.api import registrar_api
from app.routes.contas import registrar_contas
from app.routes.paginas import registrar_paginas


def register_routes(app):
    """Registra as rotas da aplicação (os nomes das funções são os endpoints usados nos templates)."""
    registrar_paginas(app)
    registrar_contas(app)
    registrar_api(app)

from flask import Flask
from app.database.conexao import inicializar_banco


def create_app():
    app = Flask(__name__)

    inicializar_banco()

    from app.routes import register_routes
    register_routes(app)

    return app
import secrets

from flask import Flask, g, request

from app.database.conexao import PASTA_DADOS, inicializar_banco


def _chave_secreta():
    """Chave que assina o cookie de sessão. Fica em data/ (fora do Git) para sobreviver ao reinício do servidor."""
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_DADOS / "secret_key"
    if not caminho.exists():
        caminho.write_text(secrets.token_hex(32), encoding="utf-8")
    return caminho.read_text(encoding="utf-8").strip()


def create_app():
    app = Flask(__name__)
    app.secret_key = _chave_secreta()
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=25 * 1024 * 1024,  # fotos de celular
    )

    inicializar_banco()

    from app.auth import registrar_autenticacao
    from app.routes import register_routes
    registrar_autenticacao(app)
    register_routes(app)

    @app.before_request
    def encerrar_aulas_com_horario_vencido():
        # Preserva o último trecho de fala enviado na hora do encerramento.
        if g.get("usuario") and request.endpoint not in {"static", "salvar_transcricao_route"}:
            from app.services.aulas_service import encerrar_aulas_vencidas
            encerrar_aulas_vencidas()

    return app

"""Sessão, login obrigatório e proteção CSRF."""
import secrets
from functools import wraps
from hmac import compare_digest

from flask import g, jsonify, redirect, request, session, url_for

from app.services.usuarios_service import obter_usuario


def token_csrf():
    """Token por sessão. Vai em <meta name="csrf-token"> e nos formulários."""
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def caminho_seguro(destino):
    """Só aceita caminhos internos (evita open redirect via ?proximo=)."""
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return None


def login_obrigatorio(funcao):
    @wraps(funcao)
    def embrulho(*args, **kwargs):
        if g.usuario is None:
            if request.path.startswith("/api/"):
                return jsonify({"erro": "Faça login para continuar"}), 401
            destino = request.path if request.method == "GET" else url_for("perfil")
            return redirect(url_for("entrar", proximo=destino))
        return funcao(*args, **kwargs)
    return embrulho


def registrar_autenticacao(app):
    @app.before_request
    def carregar_usuario_e_checar_csrf():
        g.usuario = obter_usuario(session["usuario_id"]) if "usuario_id" in session else None
        if "usuario_id" in session and g.usuario is None:
            session.clear()

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            enviado = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token") or ""
            if not compare_digest(enviado, session.get("csrf", "")):
                if request.path.startswith("/api/"):
                    return jsonify({"erro": "Sessão expirada. Recarregue a página."}), 400
                return "Sessão expirada. Volte e tente de novo.", 400

    @app.context_processor
    def variaveis_dos_templates():
        return {"usuario": g.get("usuario"), "csrf_token": token_csrf}

    @app.after_request
    def cabecalhos_de_seguranca(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "same-origin")
        return resposta

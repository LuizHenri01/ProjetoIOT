from flask import render_template, jsonify

def register_routes(app):
    """Registra as rotas da aplicação."""
    @app.route("/")
    def index():
        """Página principal, acessada pelo navegador do smartphone."""
        return render_template("index.html")

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "message": "Servidor ativo"})
from flask import render_template, jsonify, request
from app.services.fotos_service import salvar_foto


def register_routes(app):
    """Registra as rotas da aplicação."""

    @app.route("/")
    def index():
        """Página principal, acessada pelo navegador do smartphone."""
        return render_template("index.html")

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "message": "Servidor ativo"})

    @app.route("/api/fotos", methods=["POST"])
    def upload_foto():
        if "foto" not in request.files:
            return jsonify({"erro": "Nenhum arquivo enviado"}), 400

        arquivo = request.files["foto"]

        if arquivo.filename == "":
            return jsonify({"erro": "Nome de arquivo vazio"}), 400

        caminho = salvar_foto(arquivo)

        return jsonify({
            "status": "ok",
            "mensagem": "Foto salva com sucesso",
            "caminho": caminho
        }), 201
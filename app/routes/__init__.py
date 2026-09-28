from flask import render_template, jsonify, request
from app.services.fotos_service import salvar_foto
from app.services.aulas_service import iniciar_aula, encerrar_aula, obter_aula_ativa

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
        aula = obter_aula_ativa()
        if not aula:
            return jsonify({"erro": "Nenhuma aula em andamento"}), 400

        if "foto" not in request.files:
            return jsonify({"erro": "Nenhum arquivo enviado"}), 400

        arquivo = request.files["foto"]
        if arquivo.filename == "":
            return jsonify({"erro": "Nome de arquivo vazio"}), 400

        caminho = salvar_foto(arquivo, aula["id"])

        return jsonify({
            "status": "ok",
            "mensagem": "Foto salva com sucesso",
            "caminho": caminho
        }), 201

    @app.route("/api/aulas/iniciar", methods=["POST"])
    def iniciar_aula_route():
        dados = request.get_json(silent=True) or {}
        disciplina = dados.get("disciplina", "Sem nome")

        if obter_aula_ativa():
            return jsonify({"erro": "Já existe uma aula em andamento"}), 409

        aula_id = iniciar_aula(disciplina)
        return jsonify({"status": "ok", "aula_id": aula_id}), 201

    @app.route("/api/aulas/encerrar", methods=["POST"])
    def encerrar_aula_route():
        aula = obter_aula_ativa()

        if not aula:
            return jsonify({"erro": "Nenhuma aula em andamento"}), 400

        encerrar_aula(aula["id"])
        return jsonify({"status": "ok", "mensagem": "Aula encerrada"}), 200
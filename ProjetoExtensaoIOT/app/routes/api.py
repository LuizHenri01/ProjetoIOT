from flask import g, jsonify, request
from datetime import datetime

from app.auth import login_obrigatorio
from app.database.conexao import obter_conexao
from app.services.apresentacao import slug_da_disciplina
from app.services.aulas_service import (
    encerrar_aula, iniciar_aula, listar_aulas, obter_aula, obter_aula_ativa,
    remover_aulas, salvar_anotacoes,
)
from app.services.materias_service import (
    criar_materia, listar_aulas_da_materia, listar_materias, obter_materia,
)
from app.services.fotos_service import (
    EXTENSOES_PERMITIDAS, conteudo_de_imagem_valido, salvar_foto,
)
from app.services.transcricoes_service import (
    buscar_transcricoes, listar_transcricoes, salvar_transcricao,
)
from app.services.notificacoes_service import (
    chave_publica_vapid, notificar_usuario, push_disponivel,
    listar_notificacoes, marcar_notificacao_lida, marcar_todas_notificacoes_lidas,
    remover_assinatura, salvar_assinatura,
)

TAMANHO_MAXIMO_NOME = 80
TAMANHO_MAXIMO_ANOTACOES = 20000
def registrar_api(app):
    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "message": "Servidor ativo"})

    @app.route("/api/fotos", methods=["POST"])
    @login_obrigatorio
    def upload_foto():
        aula = obter_aula_ativa(g.usuario["id"])
        if not aula:
            return jsonify({"erro": "Nenhuma aula em andamento"}), 400

        arquivo = request.files.get("foto")
        if arquivo is None or arquivo.filename == "":
            return jsonify({"erro": "Nenhum arquivo enviado"}), 400

        extensao = arquivo.filename.rsplit(".", 1)[-1].lower() if "." in arquivo.filename else ""
        if extensao not in EXTENSOES_PERMITIDAS or not conteudo_de_imagem_valido(arquivo, extensao):
            return jsonify({"erro": "O arquivo não parece ser uma imagem válida."}), 400

        try:
            caminho = salvar_foto(arquivo, aula["id"])
        except OSError:
            return jsonify({"erro": "Não foi possível gravar a foto. Verifique o espaço disponível."}), 500
        notificar_usuario(g.usuario["id"], "Foto salva", f"Uma foto foi adicionada à aula {aula.get('nome_aula') or aula['disciplina']}.", "/aulas")
        return jsonify({"status": "ok", "mensagem": "Foto salva com sucesso", "caminho": caminho}), 201

    @app.route("/api/aulas/iniciar", methods=["POST"])
    @login_obrigatorio
    def iniciar_aula_route():
        dados = request.get_json(silent=True) or {}
        if obter_aula_ativa(g.usuario["id"]):
            return jsonify({"erro": "Já existe uma aula em andamento"}), 409

        materia_id = dados.get("materia_id")
        if materia_id not in (None, ""):
            try:
                materia_id = int(materia_id)
            except (TypeError, ValueError):
                return jsonify({"erro": "Escolha uma matéria válida."}), 400
        nome_aula = str(dados.get("nome_aula", "")).strip()[:100]
        if materia_id:
            materia = obter_materia(materia_id, g.usuario["id"])
            if materia is None:
                return jsonify({"erro": "Matéria não encontrada"}), 404
            if not nome_aula:
                return jsonify({"erro": "Informe o nome da aula."}), 400
            disciplina = materia["nome"]
            professor = materia["professor"]
            horario_inicio = materia["horario_inicio"]
            horario_fim_previsto = materia["horario_fim"]
        else:
            # Mantém compatibilidade com clientes antigos que ainda iniciam pela disciplina.
            disciplina = str(dados.get("disciplina", "")).strip()[:TAMANHO_MAXIMO_NOME] or "Sem nome"
            professor = str(dados.get("professor", "")).strip()[:TAMANHO_MAXIMO_NOME] or None
            horario_inicio = str(dados.get("horario_inicio", "")).strip()
            horario_fim_previsto = str(dados.get("horario_fim_previsto", "")).strip() or None
        try:
            datetime.strptime(horario_inicio, "%H:%M")
            if horario_fim_previsto:
                datetime.strptime(horario_fim_previsto, "%H:%M")
                if horario_fim_previsto <= horario_inicio:
                    return jsonify({"erro": "O horário de encerramento precisa ser depois do início."}), 400
                if materia_id and horario_fim_previsto <= datetime.now().strftime("%H:%M"):
                    # Permite registrar uma aula fora do horário previsto; ela termina manualmente.
                    horario_inicio = datetime.now().strftime("%H:%M")
                    horario_fim_previsto = None
        except ValueError:
            return jsonify({"erro": "Informe horários válidos para início e término."}), 400

        if not materia_id:
            conexao = obter_conexao()
            linha = conexao.execute(
                "SELECT id FROM materias WHERE usuario_id = ? AND lower(trim(nome)) = lower(trim(?))",
                (g.usuario["id"], disciplina),
            ).fetchone()
            conexao.close()
            if linha:
                materia_id = linha["id"]
            else:
                materia_id, erro = criar_materia(
                    g.usuario["id"], disciplina, professor or "Professor não informado",
                    horario_inicio, horario_fim_previsto or "23:59",
                )
                if erro:
                    return jsonify({"erro": erro}), 400
            nome_aula = nome_aula or f"Aula de {disciplina}"

        aula_id = iniciar_aula(
            disciplina, g.usuario["id"], professor,
            horario_inicio=horario_inicio,
            horario_fim_previsto=horario_fim_previsto,
            materia_id=materia_id,
            nome_aula=nome_aula,
        )
        notificar_usuario(g.usuario["id"], "Aula iniciada", f"{nome_aula} está em andamento.", "/captura")
        return jsonify({"status": "ok", "aula_id": aula_id}), 201

    @app.route("/api/aulas/encerrar", methods=["POST"])
    @login_obrigatorio
    def encerrar_aula_route():
        aula = obter_aula_ativa(g.usuario["id"])
        if not aula:
            return jsonify({"erro": "Nenhuma aula em andamento"}), 400

        encerrar_aula(aula["id"], g.usuario["id"])
        return jsonify({"status": "ok", "mensagem": "Aula encerrada"}), 200

    @app.route("/api/notificacoes/chave", methods=["GET"])
    @login_obrigatorio
    def chave_notificacoes_route():
        if not push_disponivel():
            return jsonify({"erro": "Instale as dependências atualizadas e reinicie o servidor."}), 503
        try:
            return jsonify({"chave": chave_publica_vapid()})
        except Exception:
            return jsonify({"erro": "Não foi possível configurar as notificações neste servidor."}), 503

    @app.route("/api/notificacoes", methods=["GET"])
    @login_obrigatorio
    def listar_notificacoes_route():
        return jsonify(listar_notificacoes(g.usuario["id"]))

    @app.route("/api/notificacoes/<int:notificacao_id>/lida", methods=["POST"])
    @login_obrigatorio
    def marcar_notificacao_lida_route(notificacao_id):
        marcar_notificacao_lida(g.usuario["id"], notificacao_id)
        return jsonify({"status": "ok"})

    @app.route("/api/notificacoes/lidas", methods=["POST"])
    @login_obrigatorio
    def marcar_todas_notificacoes_lidas_route():
        quantidade = marcar_todas_notificacoes_lidas(g.usuario["id"])
        return jsonify({"status": "ok", "marcadas": quantidade})

    @app.route("/api/notificacoes/inscricao", methods=["POST", "DELETE"])
    @login_obrigatorio
    def inscricao_notificacoes_route():
        dados = request.get_json(silent=True) or {}
        assinatura = dados.get("subscription") if request.method == "POST" else None
        if request.method == "POST":
            if not isinstance(assinatura, dict) or not salvar_assinatura(g.usuario["id"], assinatura):
                return jsonify({"erro": "Inscrição de notificações inválida."}), 400
            return jsonify({"status": "ok"}), 201
        endpoint = dados.get("endpoint", "")
        if isinstance(endpoint, str):
            remover_assinatura(g.usuario["id"], endpoint)
        return jsonify({"status": "ok"})

    @app.route("/api/notificacoes/teste", methods=["POST"])
    @login_obrigatorio
    def testar_notificacoes_route():
        resultado = notificar_usuario(
            g.usuario["id"], "Notificação de teste", "As notificações do AulaMais estão funcionando.", "/configuracoes"
        )
        if resultado["enviadas"] == 0:
            return jsonify({
                "erro": "Nenhum push foi aceito. Reative as notificações neste aparelho e confira se o servidor está usando o ambiente virtual atualizado.",
                **resultado,
            }), 502 if resultado["falhas"] else 400
        return jsonify({"status": "ok", **resultado}), 200

    @app.route("/api/aulas/<int:aula_id>", methods=["DELETE"])
    @login_obrigatorio
    def excluir_aula_route(aula_id):
        aula = obter_aula(aula_id, g.usuario["id"])
        if not aula:
            return jsonify({"erro": "Aula não encontrada"}), 404

        resultado = remover_aulas(g.usuario["id"], [aula_id])
        if resultado["status"] == "em_andamento":
            return jsonify({"erro": "Encerre a aula antes de excluí-la."}), 409
        if resultado["status"] != "removida":
            return jsonify({"erro": "Aula não encontrada"}), 404

        slug_disciplina = slug_da_disciplina(aula["disciplina"])
        restantes = sum(
            slug_da_disciplina(item["disciplina"]) == slug_disciplina
            for item in listar_aulas(g.usuario["id"])
        )
        return jsonify({
            "status": "ok", "aulas_restantes": restantes,
            "arquivos_removidos": resultado["arquivos_removidos"],
        })

    @app.route("/api/disciplinas/<slug>", methods=["DELETE"])
    @login_obrigatorio
    def excluir_disciplina_route(slug):
        materia = next(
            (item for item in listar_materias(g.usuario["id"])
             if slug_da_disciplina(item["nome"]) == slug),
            None,
        )
        if materia is None:
            return jsonify({"erro": "Matéria não encontrada"}), 404
        return excluir_materia_route(materia["id"])

    @app.route("/api/materias/<int:materia_id>", methods=["DELETE"])
    @login_obrigatorio
    def excluir_materia_route(materia_id):
        materia = obter_materia(materia_id, g.usuario["id"])
        if materia is None:
            return jsonify({"erro": "Matéria não encontrada"}), 404
        aulas_da_materia = listar_aulas_da_materia(materia_id, g.usuario["id"])
        arquivos_removidos = True
        if aulas_da_materia:
            resultado = remover_aulas(g.usuario["id"], [aula["id"] for aula in aulas_da_materia])
            if resultado["status"] == "em_andamento":
                return jsonify({"erro": "Encerre a aula em andamento antes de excluir esta matéria."}), 409
            if resultado["status"] != "removida":
                return jsonify({"erro": "Não foi possível excluir a matéria."}), 409
            arquivos_removidos = resultado["arquivos_removidos"]
        conexao = obter_conexao()
        conexao.execute("DELETE FROM materias WHERE id = ? AND usuario_id = ?", (materia_id, g.usuario["id"]))
        conexao.commit()
        conexao.close()
        return jsonify({
            "status": "ok", "aulas_removidas": len(aulas_da_materia),
            "arquivos_removidos": arquivos_removidos,
        })

    @app.route("/api/aulas/ativa", methods=["GET"])
    @login_obrigatorio
    def aula_ativa_route():
        """Informa ao navegador se existe aula em andamento (usado ao abrir/recarregar a página)."""
        return jsonify({"aula": obter_aula_ativa(g.usuario["id"])})

    @app.route("/api/transcricoes", methods=["POST"])
    @login_obrigatorio
    def salvar_transcricao_route():
        # Aceita o trecho final enviado quando o temporizador encerra a transcrição.
        aula = obter_aula_ativa(g.usuario["id"], auto_encerrar=False)
        if not aula:
            return jsonify({"erro": "Nenhuma aula em andamento"}), 400

        dados = request.get_json(silent=True) or {}
        texto = str(dados.get("texto", "")).strip()
        if not texto:
            return jsonify({"erro": "Texto vazio"}), 400

        return jsonify({"status": "ok", "transcricao": salvar_transcricao(aula["id"], texto)}), 201

    @app.route("/api/aulas/<int:aula_id>/transcricoes", methods=["GET"])
    @login_obrigatorio
    def listar_transcricoes_route(aula_id):
        if obter_aula(aula_id, g.usuario["id"]) is None:
            return jsonify({"erro": "Aula não encontrada"}), 404

        busca = request.args.get("busca", "").strip()[:100]
        if not busca:
            return jsonify({"transcricoes": listar_transcricoes(aula_id)})
        return jsonify(buscar_transcricoes(aula_id, busca))

    @app.route("/api/aulas/<int:aula_id>/anotacoes", methods=["POST"])
    @login_obrigatorio
    def salvar_anotacoes_route(aula_id):
        dados = request.get_json(silent=True) or {}
        texto = str(dados.get("texto", ""))[:TAMANHO_MAXIMO_ANOTACOES]
        if not salvar_anotacoes(aula_id, g.usuario["id"], texto):
            return jsonify({"erro": "Aula não encontrada"}), 404
        return jsonify({"status": "ok"})

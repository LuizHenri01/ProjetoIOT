from flask import flash, g, redirect, render_template, request, session, url_for

from app.auth import caminho_seguro, login_obrigatorio
from app.services.usuarios_service import (
    alterar_senha, autenticar, atualizar_dados_usuario, criar_usuario,
    atualizar_foto_perfil as salvar_foto_perfil, excluir_usuario, validar_cadastro,
    EXCLUSAO_ERRO_PREPARACAO,
    EXCLUSAO_LIMPEZA_PENDENTE, EXCLUSAO_OK, EXCLUSAO_SENHA_INCORRETA,
)


def _abrir_sessao(usuario_id):
    session.clear()  # sessão nova a cada login (evita fixação de sessão)
    session["usuario_id"] = usuario_id


def registrar_contas(app):
    @app.route("/entrar", methods=["GET", "POST"])
    def entrar():
        proximo = caminho_seguro(request.values.get("proximo"))

        if request.method == "POST":
            usuario = autenticar(request.form.get("email", ""), request.form.get("senha", ""))
            if usuario is None:
                flash("E-mail ou senha incorretos.", "erro")
                return redirect(url_for("entrar", proximo=proximo))
            _abrir_sessao(usuario["id"])
            return redirect(url_for("index"))

        return render_template("entrar.html", proximo=proximo)

    @app.route("/criar-conta", methods=["GET", "POST"])
    def criar_conta():
        if request.method == "GET":
            return render_template("criar_conta.html")

        nome = request.form.get("nome", "")
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")

        erro = validar_cadastro(nome, email, senha)
        if erro is None and not request.form.get("termos"):
            erro = "Aceite os Termos de uso e a Privacidade para criar a conta."
        if erro is None:
            usuario_id = criar_usuario(nome, email, senha)
            if usuario_id is None:
                erro = "Já existe uma conta com esse e-mail. Use Entrar."
        if erro:
            flash(erro, "erro")
            return redirect(url_for("criar_conta"))

        _abrir_sessao(usuario_id)
        return redirect(url_for("aulas"))

    @app.route("/sair")
    def sair():
        session.clear()
        return redirect(url_for("index"))

    @app.route("/perfil/atualizar", methods=["POST"])
    @login_obrigatorio
    def atualizar_perfil():
        erro = atualizar_dados_usuario(
            g.usuario["id"], request.form.get("nome"), request.form.get("email")
        )
        flash(erro or "Dados do perfil atualizados.", "erro" if erro else "info")
        return redirect(url_for("perfil"))

    @app.route("/perfil/foto", methods=["POST"])
    @login_obrigatorio
    def atualizar_foto_perfil_route():
        arquivo = request.files.get("foto")
        if arquivo is None or not arquivo.filename:
            flash("Escolha uma imagem antes de salvar.", "erro")
            return redirect(url_for("perfil"))
        erro = salvar_foto_perfil(g.usuario["id"], arquivo)
        flash(erro or "Foto do perfil atualizada.", "erro" if erro else "info")
        return redirect(url_for("perfil"))

    @app.route("/perfil/senha", methods=["POST"])
    @login_obrigatorio
    def atualizar_senha():
        erro = alterar_senha(
            g.usuario["id"], request.form.get("senha_atual", ""),
            request.form.get("senha_nova", ""),
        )
        flash(erro or "Senha alterada.", "erro" if erro else "info")
        return redirect(url_for("perfil"))

    @app.route("/perfil/excluir", methods=["POST"])
    @login_obrigatorio
    def apagar_conta():
        if request.form.get("confirmar_exclusao") != "sim":
            flash("Marque a confirmação antes de excluir a conta.", "erro")
            return redirect(url_for("perfil"))
        resultado = excluir_usuario(g.usuario["id"], request.form.get("senha_atual", ""))
        if resultado == EXCLUSAO_SENHA_INCORRETA:
            flash("A senha está incorreta. A conta não foi excluída.", "erro")
            return redirect(url_for("perfil"))

        if resultado == EXCLUSAO_ERRO_PREPARACAO or resultado not in (EXCLUSAO_OK, EXCLUSAO_LIMPEZA_PENDENTE):
            flash("Não foi possível concluir a exclusão. A conta foi mantida; peça ajuda à equipe responsável.", "erro")
            return redirect(url_for("perfil"))

        session.clear()
        if resultado == EXCLUSAO_LIMPEZA_PENDENTE:
            flash("A conta foi excluída, mas alguns arquivos locais precisam de limpeza pela equipe responsável.", "erro")
            return redirect(url_for("index"))

        flash("Conta e dados associados excluídos desta instalação.", "info")
        return redirect(url_for("index"))

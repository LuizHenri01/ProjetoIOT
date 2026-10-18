from io import BytesIO
import json
import zipfile
from pathlib import Path
from datetime import datetime

from flask import abort, flash, g, redirect, render_template, request, send_file, send_from_directory, url_for

from app.auth import login_obrigatorio
from app.database.conexao import PASTA_TRANSCRICOES
from app.services.apresentacao import hora_da_foto, id_do_slug, montar_aula, slug_da_disciplina
from app.services.aulas_service import listar_aulas, obter_aula
from app.services.materias_service import (
    criar_materia, listar_aulas_da_materia, listar_materias, obter_materia,
)
from app.services.fotos_service import listar_fotos, pasta_da_aula
from app.services.usuarios_service import PASTA_FOTOS_PERFIL
from app.services.transcricoes_service import obter_previa_transcricoes

LIMITE_PREVIA_TRANSCRICAO = 240
QUANTIDADE_PREVIA_TRANSCRICAO = 3


def registrar_paginas(app):
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/sobre")
    def sobre():
        # "Sobre" agora é uma seção da página inicial; mantém links antigos funcionando.
        return redirect(url_for("index") + "#sobre", code=301)

    @app.route("/funcionalidades")
    def funcionalidades():
        return render_template("funcionalidades.html")

    @app.route("/acessibilidade")
    def acessibilidade():
        return render_template("acessibilidade.html")

    @app.route("/aulas")
    @login_obrigatorio
    def aulas():
        materias = listar_materias(g.usuario["id"])
        for materia in materias:
            materia["slug"] = slug_da_disciplina(materia["nome"])
            materia["cor"] = ("blue", "green", "yellow", "purple", "red")[materia["id"] % 5]
            materia["ultima_aula"] = (
                datetime.strptime(materia["ultima_aula"], "%Y-%m-%d").strftime("%d/%m/%Y")
                if materia["ultima_aula"] else None
            )
        return render_template(
            "aulas.html", materias=materias,
            total_aulas=sum(materia["total_aulas"] for materia in materias),
            em_andamento=sum(materia["aulas_ativas"] or 0 for materia in materias),
        )

    @app.route("/disciplinas/criar", methods=["POST"])
    @login_obrigatorio
    def criar_disciplina_route():
        nome = request.form.get("nome", "").strip()
        professor = request.form.get("professor", "").strip()
        inicio = request.form.get("horario_inicio", "").strip()
        fim = request.form.get("horario_fim", "").strip()
        erro = None
        materia_id = None
        if not nome or len(nome) > 80:
            erro = "Informe o nome da matéria (até 80 caracteres)."
        elif not professor or len(professor) > 80:
            erro = "Informe o nome do professor (até 80 caracteres)."
        else:
            try:
                datetime.strptime(inicio, "%H:%M")
                datetime.strptime(fim, "%H:%M")
                if fim <= inicio:
                    erro = "O horário de término precisa ser depois do início."
            except ValueError:
                erro = "Informe horários válidos para a matéria."
        if erro is None:
            materia_id, erro = criar_materia(g.usuario["id"], nome, professor, inicio, fim)
        if erro:
            flash(erro, "erro")
            return redirect(url_for("aulas") + "#nova-materia")
        flash("Matéria adicionada. Agora você pode incluir aulas nela.", "info")
        return redirect(url_for("detalhe_materia", materia_id=materia_id))

    @app.route("/materias/<int:materia_id>")
    @login_obrigatorio
    def detalhe_materia(materia_id):
        materia = obter_materia(materia_id, g.usuario["id"])
        if materia is None:
            abort(404)
        aulas_da_materia = [montar_aula(linha) for linha in listar_aulas_da_materia(materia_id, g.usuario["id"])]
        materia["slug"] = slug_da_disciplina(materia["nome"])
        return render_template("disciplina.html", materia=materia, aulas=aulas_da_materia)

    @app.route("/disciplinas/<slug>")
    @login_obrigatorio
    def disciplina(slug):
        materia = next(
            (item for item in listar_materias(g.usuario["id"])
             if slug_da_disciplina(item["nome"]) == slug),
            None,
        )
        if materia is None:
            abort(404)
        return redirect(url_for("detalhe_materia", materia_id=materia["id"]), code=301)

    @app.route("/aulas/<slug>")
    @login_obrigatorio
    def detalhe_aula(slug):
        aula_id = id_do_slug(slug)
        linha = obter_aula(aula_id, g.usuario["id"]) if aula_id else None
        if linha is None:
            abort(404)

        aula = montar_aula(linha)
        aula["disciplina_slug"] = slug_da_disciplina(aula["disciplina"])
        previa = obter_previa_transcricoes(
            aula["id"], QUANTIDADE_PREVIA_TRANSCRICAO, LIMITE_PREVIA_TRANSCRICAO
        )
        fotos = [{"nome": n, "hora": hora_da_foto(n)} for n in listar_fotos(aula["id"])]

        aula["transcricoes"] = previa["transcricoes"]
        aula["transcricao_tem_mais"] = previa["tem_mais"]
        aula["fotos"] = fotos
        aula["tema"] = aula["nome"]
        aula["registro"] = f"{previa['total']} trechos de fala e {len(fotos)} fotos do quadro."
        return render_template("detalhe_aula.html", aula=aula)

    @app.route("/aulas/<int:aula_id>/transcricao.txt")
    @login_obrigatorio
    def baixar_transcricao_aula(aula_id):
        if obter_aula(aula_id, g.usuario["id"]) is None:
            abort(404)

        transcricao = PASTA_TRANSCRICOES / f"aula_{aula_id}.txt"
        if not transcricao.is_file() or transcricao.stat().st_size == 0:
            abort(404)
        return send_file(
            transcricao,
            mimetype="text/plain",
            as_attachment=True,
            download_name=f"transcricao_aula_{aula_id}.txt",
        )

    @app.route("/aulas/<int:aula_id>/fotos/<nome>")
    @login_obrigatorio
    def foto_aula(aula_id, nome):
        if obter_aula(aula_id, g.usuario["id"]) is None:
            abort(404)
        return send_from_directory(pasta_da_aula(aula_id), nome)  # recusa caminhos fora da pasta

    @app.route("/captura")
    @login_obrigatorio
    def captura():
        materias = listar_materias(g.usuario["id"])
        materia_id = request.args.get("materia", type=int)
        materia_selecionada = obter_materia(materia_id, g.usuario["id"]) if materia_id else None
        return render_template(
            "captura.html", materias=materias, materia_selecionada=materia_selecionada,
        )

    @app.route("/perfil")
    @login_obrigatorio
    def perfil():
        aulas_usuario = listar_aulas(g.usuario["id"])
        materias = listar_materias(g.usuario["id"])
        total_fotos = sum(len(listar_fotos(aula["id"])) for aula in aulas_usuario)
        nome_foto = g.usuario.get("foto_perfil")
        caminho_foto = PASTA_FOTOS_PERFIL / nome_foto if nome_foto and Path(nome_foto).name == nome_foto else None
        tem_foto_perfil = bool(
            caminho_foto
            and nome_foto.startswith(f"usuario_{g.usuario['id']}_")
            and caminho_foto.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
            and caminho_foto.is_file()
            and caminho_foto.resolve().parent == PASTA_FOTOS_PERFIL.resolve()
        )
        return render_template(
            "perfil.html", total_aulas=len(aulas_usuario),
            total_materias=len(materias), total_fotos=total_fotos,
            tem_foto_perfil=tem_foto_perfil,
        )

    @app.route("/perfil/foto")
    @login_obrigatorio
    def foto_perfil():
        nome_arquivo = g.usuario.get("foto_perfil")
        if (not nome_arquivo or Path(nome_arquivo).name != nome_arquivo
                or not nome_arquivo.startswith(f"usuario_{g.usuario['id']}_")
                or Path(nome_arquivo).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}):
            abort(404)
        caminho = PASTA_FOTOS_PERFIL / nome_arquivo
        if not caminho.is_file() or caminho.resolve().parent != PASTA_FOTOS_PERFIL.resolve():
            abort(404)
        return send_from_directory(PASTA_FOTOS_PERFIL, nome_arquivo, conditional=True)

    @app.route("/perfil/exportar")
    @login_obrigatorio
    def exportar_dados():
        pacote = BytesIO()
        lista_aulas = listar_aulas(g.usuario["id"])
        materias_exportadas = [
            {
                "id": materia["id"], "nome": materia["nome"],
                "professor": materia["professor"],
                "horario_inicio": materia["horario_inicio"],
                "horario_fim": materia["horario_fim"],
            }
            for materia in listar_materias(g.usuario["id"])
        ]
        aulas_exportadas = []
        with zipfile.ZipFile(pacote, "w", compression=zipfile.ZIP_DEFLATED) as arquivo_zip:
            foto_perfil = g.usuario.get("foto_perfil")
            foto_exportada = None
            if (foto_perfil and Path(foto_perfil).name == foto_perfil
                    and foto_perfil.startswith(f"usuario_{g.usuario['id']}_")):
                caminho_foto_perfil = PASTA_FOTOS_PERFIL / foto_perfil
                if caminho_foto_perfil.is_file():
                    foto_exportada = f"perfil/foto{caminho_foto_perfil.suffix.lower()}"
                    arquivo_zip.write(caminho_foto_perfil, foto_exportada)

            for linha in lista_aulas:
                aula_id = linha["id"]
                prefixo = f"aulas/{aula_id}"
                aulas_exportadas.append({
                    "id": aula_id,
                    "materia_id": linha.get("materia_id"),
                    "nome": linha.get("nome_aula"),
                    "disciplina": linha["disciplina"],
                    "professor": linha["professor"],
                    "data": linha["data"],
                    "horario_inicio": linha["horario_inicio"],
                    "horario_fim": linha["horario_fim"],
                    "horario_fim_previsto": linha.get("horario_fim_previsto"),
                    "anotacoes": linha["anotacoes"],
                })
                transcricao = PASTA_TRANSCRICOES / f"aula_{aula_id}.txt"
                if transcricao.is_file():
                    arquivo_zip.write(transcricao, f"{prefixo}/transcricao.txt")
                for nome in listar_fotos(aula_id):
                    foto = pasta_da_aula(aula_id) / nome
                    if foto.is_file():
                        arquivo_zip.write(foto, f"{prefixo}/fotos/{nome}")

            manifesto = {
                "projeto": "AulaMais",
                "tipo": "exportacao de dados da conta",
                "usuario": {
                    "nome": g.usuario["nome"],
                    "email": g.usuario["email"],
                    "criado_em": g.usuario["criado_em"],
                    "foto_perfil": foto_exportada,
                },
                "aulas": aulas_exportadas,
                "materias": materias_exportadas,
            }
            arquivo_zip.writestr(
                "dados.json", json.dumps(manifesto, ensure_ascii=False, indent=2)
            )

        pacote.seek(0)
        return send_file(
            pacote, mimetype="application/zip", as_attachment=True,
            download_name="aulamais-meus-dados.zip",
        )

    @app.route("/configuracoes")
    @login_obrigatorio
    def configuracoes():
        return render_template("configuracoes.html")

    @app.route("/sw.js")
    def service_worker():
        resposta = send_from_directory(app.static_folder + "/js", "sw.js", mimetype="application/javascript")
        resposta.headers["Service-Worker-Allowed"] = "/"
        resposta.headers["Cache-Control"] = "no-cache"
        return resposta

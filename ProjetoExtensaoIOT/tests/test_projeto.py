import json
from io import BytesIO
import tempfile
import unittest
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import app as app_module
from app import create_app
from app.database import conexao
from app.routes import paginas as paginas_routes
from app.services import fotos_service, transcricoes_service
from app.services.aulas_service import iniciar_aula
from app.services.transcricoes_service import obter_previa_transcricoes, salvar_transcricao
from app.services.usuarios_service import (
    EXCLUSAO_LIMPEZA_PENDENTE,
    EXCLUSAO_OK,
    criar_usuario,
    excluir_usuario,
    obter_usuario,
)
from werkzeug.datastructures import FileStorage


class AulaMaisTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.raiz_temp = Path(self.temp.name)
        self.pasta_dados = self.raiz_temp / "data"
        self.pasta_transcricoes = self.pasta_dados / "transcricoes"
        self.pasta_fotos = self.pasta_dados / "fotos"
        self.banco = self.pasta_dados / "teste.db"
        self.originais = {
            "app_dados": app_module.PASTA_DADOS,
            "dados": conexao.PASTA_DADOS,
            "banco": conexao.CAMINHO_BANCO,
            "transcricoes_db": conexao.PASTA_TRANSCRICOES,
            "transcricoes_service": transcricoes_service.PASTA_TRANSCRICOES,
            "transcricoes_pages": paginas_routes.PASTA_TRANSCRICOES,
            "fotos": fotos_service.PASTA_FOTOS,
        }
        app_module.PASTA_DADOS = self.pasta_dados
        conexao.PASTA_DADOS = self.pasta_dados
        conexao.CAMINHO_BANCO = self.banco
        conexao.PASTA_TRANSCRICOES = self.pasta_transcricoes
        transcricoes_service.PASTA_TRANSCRICOES = self.pasta_transcricoes
        paginas_routes.PASTA_TRANSCRICOES = self.pasta_transcricoes
        fotos_service.PASTA_FOTOS = self.pasta_fotos
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.cliente = self.app.test_client()

    def tearDown(self):
        app_module.PASTA_DADOS = self.originais["app_dados"]
        conexao.PASTA_DADOS = self.originais["dados"]
        conexao.CAMINHO_BANCO = self.originais["banco"]
        conexao.PASTA_TRANSCRICOES = self.originais["transcricoes_db"]
        transcricoes_service.PASTA_TRANSCRICOES = self.originais["transcricoes_service"]
        paginas_routes.PASTA_TRANSCRICOES = self.originais["transcricoes_pages"]
        fotos_service.PASTA_FOTOS = self.originais["fotos"]
        self.temp.cleanup()

    def criar_conta(self, email="teste@example.com"):
        return criar_usuario("Estudante", email, "senha-de-teste")

    def autenticar_cliente_por_sessao(self, usuario_id):
        with self.cliente.session_transaction() as sessao:
            sessao["usuario_id"] = usuario_id

    def test_login_com_credenciais_validas(self):
        self.criar_conta()
        pagina = self.cliente.get("/entrar")
        token = pagina.data.decode().split('name="csrf-token" content="', 1)[1].split('"', 1)[0]
        resposta = self.cliente.post(
            "/entrar", data={"email": "teste@example.com", "senha": "senha-de-teste", "csrf_token": token}
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(resposta.headers["Location"].split("?")[0], "/aulas")

    def test_busca_de_transcricao_limita_resultados_sem_perder_total(self):
        usuario_id = self.criar_conta()
        aula_id = iniciar_aula("Biologia", usuario_id)
        for indice in range(55):
            salvar_transcricao(aula_id, f"A árvore número {indice} tem uma raiz.")
        self.autenticar_cliente_por_sessao(usuario_id)
        resposta = self.cliente.get(f"/api/aulas/{aula_id}/transcricoes?busca=ARVORE")
        dados = resposta.get_json()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(dados["total"], 55)
        self.assertEqual(len(dados["transcricoes"]), 50)

    def test_previa_de_transcricao_e_curta(self):
        usuario_id = self.criar_conta()
        aula_id = iniciar_aula("História", usuario_id)
        for _ in range(5):
            salvar_transcricao(aula_id, "a" * 300)
        previa = obter_previa_transcricoes(aula_id)
        self.assertEqual(previa["total"], 5)
        self.assertEqual(len(previa["transcricoes"]), 3)
        self.assertEqual(len(previa["transcricoes"][0]["texto"]), 241)
        self.assertTrue(previa["tem_mais"])

    def test_exportacao_inclui_dados_transcricao_e_foto(self):
        usuario_id = self.criar_conta()
        aula_id = iniciar_aula("Matemática", usuario_id)
        salvar_transcricao(aula_id, "Conteúdo da aula")
        pasta_foto = self.pasta_fotos / f"aula_{aula_id}"
        pasta_foto.mkdir(parents=True)
        (pasta_foto / "quadro.jpg").write_bytes(b"foto")
        self.autenticar_cliente_por_sessao(usuario_id)
        resposta = self.cliente.get("/perfil/exportar")
        with zipfile.ZipFile(BytesIO(resposta.get_data())) as pacote:
            nomes = set(pacote.namelist())
            manifesto = json.loads(pacote.read("dados.json"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(f"aulas/{aula_id}/transcricao.txt", nomes)
        self.assertIn(f"aulas/{aula_id}/fotos/quadro.jpg", nomes)
        self.assertEqual(manifesto["aulas"][0]["disciplina"], "Matemática")

    def test_exclusao_remove_conta_e_arquivos(self):
        usuario_id = self.criar_conta()
        aula_id = iniciar_aula("Química", usuario_id)
        salvar_transcricao(aula_id, "Trecho")
        pasta_foto = self.pasta_fotos / f"aula_{aula_id}"
        pasta_foto.mkdir(parents=True)
        (pasta_foto / "quadro.jpg").write_bytes(b"foto")
        resultado = excluir_usuario(usuario_id, "senha-de-teste")
        self.assertEqual(resultado, EXCLUSAO_OK)
        self.assertIsNone(obter_usuario(usuario_id))
        self.assertFalse(pasta_foto.exists())
        self.assertFalse((self.pasta_transcricoes / f"aula_{aula_id}.txt").exists())

    def test_exclusao_reporta_pendencia_se_limpeza_final_falhar(self):
        usuario_id = self.criar_conta()
        aula_id = iniciar_aula("Química", usuario_id)
        salvar_transcricao(aula_id, "Trecho")
        with self.assertLogs(level="ERROR"):
            with patch("app.services.usuarios_service.shutil.rmtree", side_effect=PermissionError):
                resultado = excluir_usuario(usuario_id, "senha-de-teste")
        self.assertEqual(resultado, EXCLUSAO_LIMPEZA_PENDENTE)
        self.assertIsNone(obter_usuario(usuario_id))
        self.assertTrue(list(self.pasta_dados.glob(".exclusao-*")))

    def test_falha_no_banco_preserva_conta_e_restaura_arquivos(self):
        usuario_id = self.criar_conta()
        aula_id = iniciar_aula("Química", usuario_id)
        salvar_transcricao(aula_id, "Trecho")
        pasta_foto = self.pasta_fotos / f"aula_{aula_id}"
        pasta_foto.mkdir(parents=True)
        (pasta_foto / "quadro.jpg").write_bytes(b"foto")
        banco = conexao.obter_conexao()
        banco.execute(
            "CREATE TRIGGER impedir_exclusao BEFORE DELETE ON usuarios "
            "BEGIN SELECT RAISE(ABORT, 'falha simulada'); END"
        )
        banco.commit()
        banco.close()

        resultado = excluir_usuario(usuario_id, "senha-de-teste")

        self.assertEqual(resultado, "erro_preparacao")
        self.assertIsNotNone(obter_usuario(usuario_id))
        self.assertTrue(pasta_foto.is_dir())
        self.assertTrue((self.pasta_transcricoes / f"aula_{aula_id}.txt").is_file())
        self.assertFalse(list(self.pasta_dados.glob(".exclusao-*")))

    def test_upload_valida_assinatura_e_nao_sobrescreve_fotos(self):
        class RelogioFixo:
            @staticmethod
            def now():
                return datetime(2026, 10, 13, 12, 30, 45, 123456)

        caminhos = []
        for _ in range(2):
            arquivo = FileStorage(stream=BytesIO(b"\xff\xd8\xffconteudo"), filename="foto.jpg")
            self.assertTrue(fotos_service.conteudo_de_imagem_valido(arquivo, "jpg"))
            with patch("app.services.fotos_service.datetime", RelogioFixo):
                caminhos.append(fotos_service.salvar_foto(arquivo, 7))
        self.assertNotEqual(caminhos[0], caminhos[1])
        invalido = FileStorage(stream=BytesIO(b"texto"), filename="foto.jpg")
        self.assertFalse(fotos_service.conteudo_de_imagem_valido(invalido, "jpg"))

    def test_pagina_acessibilidade_tem_botoes_rotulados_e_status_anunciado(self):
        pagina = self.cliente.get("/acessibilidade")
        self.assertEqual(pagina.status_code, 200)
        self.assertIn(b'id="diminuir-tamanho"', pagina.data)
        self.assertIn(b'id="aumentar-tamanho"', pagina.data)
        self.assertIn(b'aria-live="polite"', pagina.data)
        self.assertNotIn(b'type="range"', pagina.data)


if __name__ == "__main__":
    unittest.main()

import sqlite3
import logging
import os
import shutil
import uuid
from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.database.conexao import PASTA_DADOS, _migrar_materias, obter_conexao
from app.services.fotos_service import conteudo_de_imagem_valido

EXCLUSAO_OK = "excluida"
EXCLUSAO_SENHA_INCORRETA = "senha_incorreta"
EXCLUSAO_ERRO_PREPARACAO = "erro_preparacao"
EXCLUSAO_LIMPEZA_PENDENTE = "limpeza_pendente"

# Hash com sal embutido: calculado uma vez para comparar mesmo quando o e-mail não existe.
_HASH_FALSO = generate_password_hash("senha-inexistente")
PASTA_FOTOS_PERFIL = PASTA_DADOS / "fotos_perfil"
EXTENSOES_FOTO_PERFIL = {"jpg", "jpeg", "png", "webp"}
TAMANHO_MAXIMO_FOTO_PERFIL = 5 * 1024 * 1024


def _normalizar_email(email):
    return str(email or "").strip().lower()


def validar_cadastro(nome, email, senha):
    """Devolve uma mensagem de erro, ou None se está tudo certo."""
    if not nome.strip() or len(nome.strip()) > 80:
        return "Informe seu nome (até 80 letras)."
    if "@" not in email or len(email) > 120:
        return "Informe um e-mail válido."
    if len(senha) < 6:
        return "A senha precisa ter pelo menos 6 caracteres."
    if len(senha) > 128:
        return "A senha pode ter no máximo 128 caracteres."
    return None


def criar_usuario(nome, email, senha):
    """Cria a conta. Devolve o id, ou None se o e-mail já existe."""
    email = _normalizar_email(email)
    conexao = obter_conexao()
    try:
        primeiro = conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0
        cursor = conexao.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, criado_em) VALUES (?, ?, ?, ?)",
            (nome.strip(), email, generate_password_hash(senha), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        usuario_id = cursor.lastrowid
        if primeiro:
            # As aulas gravadas antes do login existir passam a ser da primeira conta.
            conexao.execute("UPDATE aulas SET usuario_id = ? WHERE usuario_id IS NULL", (usuario_id,))
            _migrar_materias(conexao)
        conexao.commit()
        return usuario_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conexao.close()


def autenticar(email, senha):
    conexao = obter_conexao()
    linha = conexao.execute(
        "SELECT * FROM usuarios WHERE email = ?", (_normalizar_email(email),)
    ).fetchone()
    conexao.close()

    if linha is None:
        check_password_hash(_HASH_FALSO, senha)  # gasta o mesmo tempo: não revela se o e-mail existe
        return None
    return dict(linha) if check_password_hash(linha["senha_hash"], senha) else None


def obter_usuario(usuario_id):
    conexao = obter_conexao()
    linha = conexao.execute(
        "SELECT id, nome, email, criado_em, foto_perfil FROM usuarios WHERE id = ?", (usuario_id,)
    ).fetchone()
    conexao.close()
    return dict(linha) if linha else None


def atualizar_foto_perfil(usuario_id, arquivo):
    """Valida e substitui a foto de perfil por um arquivo de imagem suportado."""
    nome_original = str(getattr(arquivo, "filename", "") or "")
    extensao = nome_original.rsplit(".", 1)[-1].lower() if "." in nome_original else ""
    if extensao not in EXTENSOES_FOTO_PERFIL or not conteudo_de_imagem_valido(arquivo, extensao):
        return "Escolha uma imagem JPG, PNG ou WebP válida."

    try:
        arquivo.stream.seek(0, os.SEEK_END)
        tamanho = arquivo.stream.tell()
        arquivo.stream.seek(0)
    except (AttributeError, OSError):
        return "Não foi possível ler o arquivo enviado."
    if tamanho == 0:
        return "O arquivo de imagem está vazio."
    if tamanho > TAMANHO_MAXIMO_FOTO_PERFIL:
        return "A imagem precisa ter no máximo 5 MB."

    dados = arquivo.stream.read(TAMANHO_MAXIMO_FOTO_PERFIL + 1)
    arquivo.stream.seek(0)
    if len(dados) > TAMANHO_MAXIMO_FOTO_PERFIL:
        return "A imagem precisa ter no máximo 5 MB."

    conexao = obter_conexao()
    novo_caminho = None
    try:
        usuario = conexao.execute(
            "SELECT foto_perfil FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        if usuario is None:
            return "Não foi possível localizar a conta."

        PASTA_FOTOS_PERFIL.mkdir(parents=True, exist_ok=True, mode=0o700)
        nome_arquivo = f"usuario_{usuario_id}_{uuid.uuid4().hex}.{extensao}"
        novo_caminho = PASTA_FOTOS_PERFIL / nome_arquivo
        descritor = os.open(novo_caminho, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descritor, "wb") as destino:
            destino.write(dados)

        conexao.execute(
            "UPDATE usuarios SET foto_perfil = ? WHERE id = ?",
            (nome_arquivo, usuario_id),
        )
        conexao.commit()
        foto_anterior = usuario["foto_perfil"]
    except OSError:
        conexao.rollback()
        if novo_caminho:
            try:
                novo_caminho.unlink(missing_ok=True)
            except OSError:
                logging.exception("Não foi possível remover a foto temporária da conta %s", usuario_id)
        logging.exception("Não foi possível salvar a foto de perfil da conta %s", usuario_id)
        return "Não foi possível salvar a foto. Tente novamente."
    except sqlite3.Error:
        conexao.rollback()
        if novo_caminho:
            try:
                novo_caminho.unlink(missing_ok=True)
            except OSError:
                logging.exception("Não foi possível remover a foto temporária da conta %s", usuario_id)
        logging.exception("Não foi possível atualizar a foto de perfil da conta %s", usuario_id)
        return "Não foi possível atualizar sua foto. Tente novamente."
    finally:
        conexao.close()

    _remover_foto_antiga(usuario_id, foto_anterior)
    return None


def _remover_foto_antiga(usuario_id, nome_arquivo):
    if not nome_arquivo or os.path.basename(nome_arquivo) != nome_arquivo:
        return
    if not nome_arquivo.startswith(f"usuario_{usuario_id}_"):
        return
    caminho = PASTA_FOTOS_PERFIL / nome_arquivo
    try:
        if caminho.resolve().parent == PASTA_FOTOS_PERFIL.resolve():
            caminho.unlink(missing_ok=True)
    except OSError:
        logging.exception("Não foi possível remover a foto de perfil antiga da conta %s", usuario_id)


def atualizar_dados_usuario(usuario_id, nome, email):
    nome = str(nome or "").strip()
    email = _normalizar_email(email)
    if not nome or len(nome) > 80:
        return "Informe seu nome (até 80 letras)."
    if "@" not in email or len(email) > 120:
        return "Informe um e-mail válido."

    conexao = obter_conexao()
    try:
        conexao.execute(
            "UPDATE usuarios SET nome = ?, email = ? WHERE id = ?",
            (nome, email, usuario_id),
        )
        conexao.commit()
        return None
    except sqlite3.IntegrityError:
        return "Já existe uma conta com esse e-mail."
    finally:
        conexao.close()


def alterar_senha(usuario_id, senha_atual, senha_nova):
    if len(senha_nova) < 6 or len(senha_nova) > 128:
        return "A nova senha precisa ter entre 6 e 128 caracteres."

    conexao = obter_conexao()
    try:
        linha = conexao.execute(
            "SELECT senha_hash FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        if linha is None or not check_password_hash(linha["senha_hash"], senha_atual):
            return "A senha atual está incorreta."
        conexao.execute(
            "UPDATE usuarios SET senha_hash = ? WHERE id = ?",
            (generate_password_hash(senha_nova), usuario_id),
        )
        conexao.commit()
        return None
    finally:
        conexao.close()


def excluir_usuario(usuario_id, senha_atual):
    from app.database.conexao import PASTA_DADOS, PASTA_TRANSCRICOES
    from app.services.fotos_service import PASTA_FOTOS

    conexao = obter_conexao()
    arquivos_movidos = []
    pasta_temporaria = None
    try:
        linha = conexao.execute(
            "SELECT senha_hash, foto_perfil FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        if linha is None or not check_password_hash(linha["senha_hash"], senha_atual):
            return EXCLUSAO_SENHA_INCORRETA

        aula_ids = [linha["id"] for linha in conexao.execute(
            "SELECT id FROM aulas WHERE usuario_id = ?", (usuario_id,)
        ).fetchall()]

        arquivos = []
        for aula_id in aula_ids:
            arquivos.extend([
                (PASTA_FOTOS / f"aula_{aula_id}", f"aula_{aula_id}-fotos"),
                (PASTA_TRANSCRICOES / f"aula_{aula_id}.txt", f"aula_{aula_id}-transcricao.txt"),
            ])
        foto_perfil = linha["foto_perfil"]
        if (foto_perfil and os.path.basename(foto_perfil) == foto_perfil
                and foto_perfil.startswith(f"usuario_{usuario_id}_")):
            arquivos.append((PASTA_FOTOS_PERFIL / foto_perfil, "foto-perfil"))
        existentes = [(origem, nome) for origem, nome in arquivos if origem.exists()]
        if existentes:
            pasta_temporaria = PASTA_DADOS / f".exclusao-{uuid.uuid4().hex}"
            pasta_temporaria.mkdir(mode=0o700)
            for origem, nome in existentes:
                destino = pasta_temporaria / nome
                os.replace(origem, destino)
                arquivos_movidos.append((destino, origem))

        conexao.execute("DELETE FROM aulas WHERE usuario_id = ?", (usuario_id,))
        conexao.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conexao.commit()
    except (OSError, sqlite3.Error):
        conexao.rollback()
        restauracao_ok = True
        for origem, destino in reversed(arquivos_movidos):
            try:
                destino.parent.mkdir(parents=True, exist_ok=True)
                os.replace(origem, destino)
            except OSError:
                restauracao_ok = False
                logging.exception("Não foi possível restaurar um arquivo durante a exclusão da conta")
        if pasta_temporaria and pasta_temporaria.exists() and restauracao_ok:
            try:
                pasta_temporaria.rmdir()
            except OSError:
                logging.exception("Não foi possível remover a pasta temporária vazia da exclusão")
        if not restauracao_ok:
            return EXCLUSAO_ERRO_PREPARACAO
        return EXCLUSAO_ERRO_PREPARACAO
    finally:
        conexao.close()

    if pasta_temporaria:
        try:
            shutil.rmtree(pasta_temporaria)
        except OSError:
            logging.exception("Conta excluída, mas sobraram arquivos na pasta temporária %s", pasta_temporaria)
            return EXCLUSAO_LIMPEZA_PENDENTE
    return EXCLUSAO_OK

import os
from datetime import datetime
from werkzeug.utils import secure_filename
from app.database.conexao import obter_conexao

PASTA_FOTOS = os.path.join("data", "fotos")


def salvar_foto(arquivo, aula_id):
    os.makedirs(PASTA_FOTOS, exist_ok=True)
    agora = datetime.now()
    timestamp = agora.strftime("%Y%m%d-%H%M%S")
    extensao = secure_filename(arquivo.filename).rsplit(".", 1)[-1] if "." in arquivo.filename else "jpg"
    nome_arquivo = f"{timestamp}.{extensao}"

    caminho_completo = os.path.join(PASTA_FOTOS, nome_arquivo)
    arquivo.save(caminho_completo)

    conexao = obter_conexao()
    conexao.execute(
        "INSERT INTO fotos (aula_id, timestamp, caminho_imagem) VALUES (?, ?, ?)",
        (aula_id, agora.strftime("%H:%M:%S"), caminho_completo)
    )
    conexao.commit()
    conexao.close()

    return caminho_completo
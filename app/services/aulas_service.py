from datetime import datetime
from app.database.conexao import obter_conexao


def iniciar_aula(disciplina):
    """Cria uma nova aula com horário de início agora, sem horário de fim."""
    agora = datetime.now()

    conexao = obter_conexao()
    cursor = conexao.execute(
        "INSERT INTO aulas (disciplina, data, horario_inicio) VALUES (?, ?, ?)",
        (disciplina, agora.strftime("%Y-%m-%d"), agora.strftime("%H:%M:%S"))
    )
    conexao.commit()
    aula_id = cursor.lastrowid
    conexao.close()

    return aula_id


def encerrar_aula(aula_id):
    """Marca o horário de fim da aula."""
    agora = datetime.now().strftime("%H:%M:%S")
# Esses ? abaixo, é para proteger contra SQL Injection. Voces que forem mexer no codigo ai, nunca faça:
# conexao.execute(f"UPDATE aulas SET horario_fim = '{agora}' WHERE id
    conexao = obter_conexao()
    conexao.execute(
        "UPDATE aulas SET horario_fim = ? WHERE id = ?",
        (agora, aula_id)
    )
    conexao.commit()
    conexao.close()


def obter_aula_ativa():
    conexao = obter_conexao()
    linha = conexao.execute(
        "SELECT * FROM aulas WHERE horario_fim IS NULL ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conexao.close()

    return dict(linha) if linha else None
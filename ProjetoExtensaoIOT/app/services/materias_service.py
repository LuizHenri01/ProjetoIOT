from datetime import datetime
import sqlite3

from app.database.conexao import obter_conexao


def listar_materias(usuario_id):
    conexao = obter_conexao()
    linhas = conexao.execute(
        "SELECT m.*, COUNT(a.id) AS total_aulas, "
        "SUM(CASE WHEN a.id IS NOT NULL AND a.horario_fim IS NULL THEN 1 ELSE 0 END) AS aulas_ativas, "
        "MAX(a.data) AS ultima_aula "
        "FROM materias m LEFT JOIN aulas a ON a.materia_id = m.id "
        "WHERE m.usuario_id = ? GROUP BY m.id ORDER BY lower(m.nome)",
        (usuario_id,),
    ).fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


def obter_materia(materia_id, usuario_id):
    conexao = obter_conexao()
    linha = conexao.execute(
        "SELECT m.*, COUNT(a.id) AS total_aulas, "
        "SUM(CASE WHEN a.id IS NOT NULL AND a.horario_fim IS NULL THEN 1 ELSE 0 END) AS aulas_ativas "
        "FROM materias m LEFT JOIN aulas a ON a.materia_id = m.id "
        "WHERE m.id = ? AND m.usuario_id = ? GROUP BY m.id",
        (materia_id, usuario_id),
    ).fetchone()
    conexao.close()
    return dict(linha) if linha else None


def criar_materia(usuario_id, nome, professor, horario_inicio, horario_fim):
    conexao = obter_conexao()
    try:
        cursor = conexao.execute(
            "INSERT INTO materias (usuario_id, nome, professor, horario_inicio, horario_fim, criado_em) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (usuario_id, nome.strip(), professor.strip() or None, horario_inicio,
             horario_fim or None, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conexao.commit()
        return cursor.lastrowid, None
    except sqlite3.IntegrityError as erro:
        conexao.rollback()
        if "UNIQUE constraint failed" in str(erro):
            return None, "Você já tem uma matéria com esse nome."
        raise
    finally:
        conexao.close()


def listar_aulas_da_materia(materia_id, usuario_id):
    conexao = obter_conexao()
    linhas = conexao.execute(
        "SELECT * FROM aulas WHERE materia_id = ? AND usuario_id = ? "
        "ORDER BY data DESC, horario_inicio DESC, id DESC",
        (materia_id, usuario_id),
    ).fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]

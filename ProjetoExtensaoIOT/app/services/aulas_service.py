from datetime import datetime
import logging
import shutil

from app.database.conexao import PASTA_TRANSCRICOES, obter_conexao

logger = logging.getLogger(__name__)


def iniciar_aula(disciplina, usuario_id, professor=None, horario_inicio=None,
                 horario_fim_previsto=None, materia_id=None, nome_aula=None):
    """Cria uma aula e guarda os horários informados para o registro e o encerramento automático."""
    agora = datetime.now()
    horario_inicio = horario_inicio or agora.strftime("%H:%M")

    conexao = obter_conexao()
    cursor = conexao.execute(
        "INSERT INTO aulas (disciplina, data, horario_inicio, horario_fim_previsto, usuario_id, professor, materia_id, nome_aula) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (disciplina, agora.strftime("%Y-%m-%d"), horario_inicio, horario_fim_previsto,
         usuario_id, professor, materia_id, nome_aula),
    )
    conexao.commit()
    aula_id = cursor.lastrowid
    conexao.close()

    return aula_id


def encerrar_aula(aula_id, usuario_id, horario_fim=None):
    """Marca o horário de fim da aula (só se ela for da conta)."""
    horario_fim = horario_fim or datetime.now().strftime("%H:%M:%S")
    # Os ? protegem contra SQL Injection: nunca monte o SQL com f-string.
    conexao = obter_conexao()
    conexao.execute(
        "UPDATE aulas SET horario_fim = ? WHERE id = ? AND usuario_id = ? AND horario_fim IS NULL",
        (horario_fim, aula_id, usuario_id),
    )
    conexao.commit()
    conexao.close()


def obter_aula_ativa(usuario_id, auto_encerrar=True):
    conexao = obter_conexao()
    linha = conexao.execute(
        "SELECT * FROM aulas WHERE horario_fim IS NULL AND usuario_id = ? ORDER BY id DESC LIMIT 1",
        (usuario_id,),
    ).fetchone()
    conexao.close()

    if not linha:
        return None

    aula = dict(linha)
    horario_previsto = aula.get("horario_fim_previsto")
    if horario_previsto and auto_encerrar:
        limite = datetime.strptime(
            f"{aula['data']} {horario_previsto[:5]}", "%Y-%m-%d %H:%M"
        )
        if datetime.now() >= limite:
            encerrar_aula(aula["id"], usuario_id, horario_fim=horario_previsto)
            return None

    return aula


def encerrar_aulas_vencidas():
    """Fecha sessões cujo horário previsto já passou, mesmo sem a página de captura aberta."""
    agora = datetime.now()
    conexao = obter_conexao()
    linhas = conexao.execute(
        "SELECT id, usuario_id, data, horario_fim_previsto FROM aulas "
        "WHERE horario_fim IS NULL AND horario_fim_previsto IS NOT NULL"
    ).fetchall()
    vencidas = []
    for linha in linhas:
        aula = dict(linha)
        limite = datetime.strptime(
            f"{aula['data']} {aula['horario_fim_previsto'][:5]}", "%Y-%m-%d %H:%M"
        )
        if agora >= limite:
            vencidas.append(aula)
    for aula in vencidas:
        conexao.execute(
            "UPDATE aulas SET horario_fim = ? WHERE id = ? AND usuario_id = ? AND horario_fim IS NULL",
            (aula["horario_fim_previsto"], aula["id"], aula["usuario_id"]),
        )
    conexao.commit()
    conexao.close()
    return len(vencidas)


def listar_aulas(usuario_id):
    conexao = obter_conexao()
    linhas = conexao.execute(
        "SELECT * FROM aulas WHERE usuario_id = ? ORDER BY data DESC, horario_inicio DESC",
        (usuario_id,),
    ).fetchall()
    conexao.close()
    return [dict(linha) for linha in linhas]


def obter_aula(aula_id, usuario_id):
    """Devolve a aula só se ela pertence à conta (uma conta nunca enxerga a aula de outra)."""
    conexao = obter_conexao()
    linha = conexao.execute(
        "SELECT * FROM aulas WHERE id = ? AND usuario_id = ?", (aula_id, usuario_id)
    ).fetchone()
    conexao.close()
    return dict(linha) if linha else None


def salvar_anotacoes(aula_id, usuario_id, texto):
    conexao = obter_conexao()
    cursor = conexao.execute(
        "UPDATE aulas SET anotacoes = ? WHERE id = ? AND usuario_id = ?",
        (texto, aula_id, usuario_id),
    )
    conexao.commit()
    conexao.close()
    return cursor.rowcount == 1


def remover_aulas(usuario_id, aula_ids):
    """Remove aulas da conta e os arquivos associados, sem aceitar aulas de terceiros."""
    ids = sorted({int(aula_id) for aula_id in aula_ids})
    if not ids:
        return {"status": "nao_encontrada", "arquivos_removidos": True}

    marcadores = ",".join("?" for _ in ids)
    conexao = obter_conexao()
    try:
        conexao.execute("BEGIN IMMEDIATE")
        linhas = conexao.execute(
            f"SELECT id, horario_fim FROM aulas WHERE usuario_id = ? AND id IN ({marcadores})",
            [usuario_id, *ids],
        ).fetchall()
        if len(linhas) != len(ids):
            conexao.rollback()
            return {"status": "nao_encontrada", "arquivos_removidos": True}
        if any(linha["horario_fim"] is None for linha in linhas):
            conexao.rollback()
            return {"status": "em_andamento", "arquivos_removidos": True}

        conexao.execute(
            f"DELETE FROM aulas WHERE usuario_id = ? AND id IN ({marcadores})",
            [usuario_id, *ids],
        )
        conexao.commit()
    finally:
        conexao.close()

    arquivos_removidos = True
    for aula_id in ids:
        try:
            _remover_arquivos_aula(aula_id)
        except OSError:
            arquivos_removidos = False
            logger.exception("Não foi possível remover todos os arquivos da aula %s", aula_id)

    return {"status": "removida", "quantidade": len(ids), "arquivos_removidos": arquivos_removidos}


def _remover_arquivos_aula(aula_id):
    """Remove apenas o diretório e a transcrição pertencentes ao ID da aula."""
    from app.services.fotos_service import PASTA_FOTOS, pasta_da_aula

    raiz_fotos = PASTA_FOTOS.resolve()
    pasta_fotos = pasta_da_aula(aula_id)
    if pasta_fotos.exists():
        caminho_fotos = pasta_fotos.resolve()
        if caminho_fotos.parent != raiz_fotos:
            raise OSError("O diretório das fotos não corresponde à pasta da aula")
        shutil.rmtree(caminho_fotos)

    raiz_transcricoes = PASTA_TRANSCRICOES.resolve()
    arquivo_transcricao = PASTA_TRANSCRICOES / f"aula_{aula_id}.txt"
    if arquivo_transcricao.exists():
        caminho_transcricao = arquivo_transcricao.resolve()
        if caminho_transcricao.parent != raiz_transcricoes or caminho_transcricao.name != f"aula_{aula_id}.txt":
            raise OSError("O arquivo de transcrição não corresponde à aula")
        caminho_transcricao.unlink()

import sqlite3
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parents[2]
PASTA_DADOS = RAIZ_PROJETO / "data"
CAMINHO_BANCO = PASTA_DADOS / "banco.db"
CAMINHO_SCHEMA = Path(__file__).resolve().with_name("schema.sql")
PASTA_TRANSCRICOES = PASTA_DADOS / "transcricoes"


def obter_conexao():
    PASTA_DADOS.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row

    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


def _tabela_existe(conexao, nome):
    return conexao.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (nome,)
    ).fetchone() is not None


def _migrar_transcricoes_para_arquivos(conexao):
    linhas = conexao.execute(
        "SELECT aula_id, timestamp, texto FROM transcricoes ORDER BY aula_id, id"
    ).fetchall()

    if not linhas:
        return

    PASTA_TRANSCRICOES.mkdir(parents=True, exist_ok=True)
    transcricoes_por_aula = {}
    for linha in linhas:
        texto = " ".join(linha["texto"].split())
        registro = f'{linha["timestamp"]} - {texto}\n'
        transcricoes_por_aula.setdefault(linha["aula_id"], []).append(registro)

    for aula_id, registros in transcricoes_por_aula.items():
        caminho = PASTA_TRANSCRICOES / f"aula_{aula_id}.txt"
        caminho.write_text("".join(registros), encoding="utf-8")


COLUNAS_NOVAS_AULAS = {
    "usuario_id": "INTEGER REFERENCES usuarios(id)",
    "professor": "TEXT",
    "anotacoes": "TEXT NOT NULL DEFAULT ''",
    "horario_fim_previsto": "TEXT",
    "materia_id": "INTEGER REFERENCES materias(id) ON DELETE CASCADE",
    "nome_aula": "TEXT",
}

COLUNAS_NOVAS_USUARIOS = {
    "foto_perfil": "TEXT",
}


def _migrar_colunas_aulas(conexao):
    """Bancos criados antes do login não têm essas colunas: acrescenta sem apagar nada."""
    existentes = {linha["name"] for linha in conexao.execute("PRAGMA table_info(aulas)")}
    for nome, definicao in COLUNAS_NOVAS_AULAS.items():
        if nome not in existentes:
            conexao.execute(f"ALTER TABLE aulas ADD COLUMN {nome} {definicao}")


def _migrar_colunas_usuarios(conexao):
    existentes = {linha["name"] for linha in conexao.execute("PRAGMA table_info(usuarios)")}
    for nome, definicao in COLUNAS_NOVAS_USUARIOS.items():
        if nome not in existentes:
            conexao.execute(f"ALTER TABLE usuarios ADD COLUMN {nome} {definicao}")


def _migrar_materias(conexao):
    """Cria matérias a partir dos registros antigos e associa cada aula existente."""
    conexao.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_materias_usuario_nome "
        "ON materias(usuario_id, lower(trim(nome)))"
    )
    conexao.execute(
        "INSERT OR IGNORE INTO materias "
        "(usuario_id, nome, professor, horario_inicio, horario_fim, criado_em) "
        "SELECT usuario_id, MIN(trim(disciplina)), MIN(professor), "
        "MIN(horario_inicio), MAX(horario_fim_previsto), MIN(data) || ' 00:00:00' "
        "FROM aulas WHERE usuario_id IS NOT NULL AND trim(disciplina) != '' "
        "GROUP BY usuario_id, lower(trim(disciplina))"
    )
    conexao.execute(
        "UPDATE aulas SET materia_id = ("
        "SELECT materias.id FROM materias "
        "WHERE materias.usuario_id = aulas.usuario_id "
        "AND lower(trim(materias.nome)) = lower(trim(aulas.disciplina)) LIMIT 1) "
        "WHERE materia_id IS NULL AND usuario_id IS NOT NULL"
    )
    conexao.execute(
        "UPDATE aulas SET nome_aula = 'Aula ' || data WHERE nome_aula IS NULL"
    )


def inicializar_banco():
    conexao = obter_conexao()
    try:
        schema = CAMINHO_SCHEMA.read_text(encoding="utf-8")
        conexao.executescript(schema)
        _migrar_colunas_aulas(conexao)
        _migrar_colunas_usuarios(conexao)
        _migrar_materias(conexao)

        if _tabela_existe(conexao, "transcricoes"):
            _migrar_transcricoes_para_arquivos(conexao)
            conexao.execute("DROP TABLE transcricoes")

        if _tabela_existe(conexao, "fotos"):
            conexao.execute("DROP TABLE fotos")

        conexao.commit()
    finally:
        conexao.close()

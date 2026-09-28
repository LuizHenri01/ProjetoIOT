import sqlite3
import os

CAMINHO_BANCO = os.path.join("data", "banco.db")
CAMINHO_SCHEMA = os.path.join("app", "database", "schema.sql")


def obter_conexao():
    os.makedirs(os.path.dirname(CAMINHO_BANCO), exist_ok=True)

    conexao = sqlite3.connect(CAMINHO_BANCO)
    conexao.row_factory = sqlite3.Row

    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao

def inicializar_banco():
    
    with open(CAMINHO_SCHEMA, "r", encoding="utf-8") as f:
        schema = f.read()

    conexao = obter_conexao()
    conexao.executescript(schema)
    conexao.commit()
    conexao.close()
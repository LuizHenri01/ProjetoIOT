CREATE TABLE IF NOT EXISTS aulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disciplina TEXT NOT NULL,
    data TEXT NOT NULL,
    horario_inicio TEXT NOT NULL,
    horario_fim TEXT
);

CREATE TABLE IF NOT EXISTS transcricoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aula_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    texto TEXT NOT NULL,
    FOREIGN KEY (aula_id) REFERENCES aulas (id)
);

CREATE TABLE IF NOT EXISTS fotos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    aula_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    caminho_imagem TEXT NOT NULL,
    FOREIGN KEY (aula_id) REFERENCES aulas (id)
);
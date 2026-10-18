CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL,
    criado_em TEXT NOT NULL,
    foto_perfil TEXT
);

CREATE TABLE IF NOT EXISTS materias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    professor TEXT,
    horario_inicio TEXT NOT NULL,
    horario_fim TEXT,
    criado_em TEXT NOT NULL,
    UNIQUE(usuario_id, nome)
);

CREATE TABLE IF NOT EXISTS aulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    disciplina TEXT NOT NULL,
    data TEXT NOT NULL,
    horario_inicio TEXT NOT NULL,
    horario_fim TEXT,
    horario_fim_previsto TEXT,
    usuario_id INTEGER REFERENCES usuarios(id),
    professor TEXT,
    anotacoes TEXT NOT NULL DEFAULT '',
    materia_id INTEGER REFERENCES materias(id) ON DELETE CASCADE,
    nome_aula TEXT
);

CREATE TABLE IF NOT EXISTS notificacoes_push (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL UNIQUE,
    assinatura_json TEXT NOT NULL,
    criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notificacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    titulo TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '/aulas',
    criada_em TEXT NOT NULL,
    lida_em TEXT
);

CREATE INDEX IF NOT EXISTS idx_notificacoes_usuario_data
ON notificacoes(usuario_id, criada_em DESC);

-- Esquema do banco de dados para o VetBooking

-- Tabela para tutores (donos de pets)
CREATE TABLE IF NOT EXISTS tutores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    endereco TEXT NOT NULL,
    cep TEXT NOT NULL,
    data_nascimento TEXT NOT NULL,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para médicos veterinários
CREATE TABLE IF NOT EXISTS medicos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    crmv TEXT NOT NULL,
    uf TEXT NOT NULL,
    especialidades TEXT,
    descricao TEXT,
    foto TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para clínicas veterinárias
CREATE TABLE IF NOT EXISTS clinicas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    razao_social TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    cep TEXT NOT NULL,
    uf TEXT NOT NULL,
    cidade TEXT NOT NULL,
    bairro TEXT NOT NULL,
    rua TEXT NOT NULL,
    numero TEXT NOT NULL,
    complemento TEXT,
    telefone TEXT,
    horario_funcionamento TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para pets
CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    especie TEXT NOT NULL,
    raca TEXT,
    data_nascimento TEXT,
    sexo TEXT,
    peso REAL,
    tutor_id INTEGER NOT NULL,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tutor_id) REFERENCES tutores (id)
);

-- Tabela para médicos que trabalham em clínicas
CREATE TABLE IF NOT EXISTS medicos_clinicas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medico_id INTEGER NOT NULL,
    clinica_id INTEGER NOT NULL,
    dias_atendimento TEXT,
    horarios_atendimento TEXT,
    FOREIGN KEY (medico_id) REFERENCES medicos (id),
    FOREIGN KEY (clinica_id) REFERENCES clinicas (id)
);

-- Tabela para agendamentos
CREATE TABLE IF NOT EXISTS agendamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT NOT NULL,
    pet_id INTEGER NOT NULL,
    medico_id INTEGER NOT NULL,
    clinica_id INTEGER,
    status TEXT NOT NULL DEFAULT 'agendado',
    observacoes TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pet_id) REFERENCES pets (id),
    FOREIGN KEY (medico_id) REFERENCES medicos (id),
    FOREIGN KEY (clinica_id) REFERENCES clinicas (id)
);

-- Tabela para favoritos (tutores podem favoritar médicos)
CREATE TABLE IF NOT EXISTS favoritos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tutor_id INTEGER NOT NULL,
    medico_id INTEGER NOT NULL,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tutor_id) REFERENCES tutores (id),
    FOREIGN KEY (medico_id) REFERENCES medicos (id),
    UNIQUE(tutor_id, medico_id)
);
-- Banco de dados para o sistema de leilão (SQLite version)

-- Tabela de Usuários (base para Cliente e Admin)
CREATE TABLE IF NOT EXISTS Usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    sobrenome TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Cliente
CREATE TABLE IF NOT EXISTS Cliente (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER UNIQUE NOT NULL,
    telefone TEXT,
    cpf TEXT UNIQUE,
    endereco TEXT,
    cidade TEXT,
    estado TEXT,
    cep TEXT,
    status TEXT CHECK(status IN ('ativo', 'inativo', 'bloqueado')) DEFAULT 'ativo',
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

-- Tabela de Admin
CREATE TABLE IF NOT EXISTS Admin (
    id_admin INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER UNIQUE NOT NULL,
    nivel_acesso TEXT CHECK(nivel_acesso IN ('básico', 'intermediário', 'total')) DEFAULT 'básico',
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario) ON DELETE CASCADE
);

-- Tabela de Categorias de Veículos
CREATE TABLE IF NOT EXISTS Categoria (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    descricao TEXT
);

-- Tabela de Carros
CREATE TABLE IF NOT EXISTS Carro (
    id_carro INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    ano INTEGER,
    placa TEXT,
    quilometragem INTEGER,
    cor TEXT,
    id_categoria INTEGER,
    preco_inicial REAL NOT NULL,
    descricao TEXT,
    condicao TEXT CHECK(condicao IN ('novo', 'seminovo', 'usado')) DEFAULT 'usado',
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    id_admin INTEGER,
    FOREIGN KEY (id_categoria) REFERENCES Categoria(id_categoria),
    FOREIGN KEY (id_admin) REFERENCES Admin(id_admin)
);

-- Tabela de Imagens de Carros
CREATE TABLE IF NOT EXISTS Imagem_Carro (
    id_imagem INTEGER PRIMARY KEY AUTOINCREMENT,
    id_carro INTEGER,
    url_imagem TEXT NOT NULL,
    principal INTEGER DEFAULT 0,
    FOREIGN KEY (id_carro) REFERENCES Carro(id_carro) ON DELETE CASCADE
);

-- Tabela de Leilão
CREATE TABLE IF NOT EXISTS Leilao (
    id_leilao INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descricao TEXT,
    id_carro INTEGER UNIQUE,
    data_inicio DATETIME NOT NULL,
    data_fim DATETIME NOT NULL,
    preco_minimo REAL NOT NULL,
    incremento_minimo REAL DEFAULT 100.00,
    status TEXT CHECK(status IN ('agendado', 'aberto', 'encerrado', 'cancelado')) DEFAULT 'agendado',
    id_admin INTEGER,
    FOREIGN KEY (id_carro) REFERENCES Carro(id_carro),
    FOREIGN KEY (id_admin) REFERENCES Admin(id_admin)
);

-- Tabela de Lances
CREATE TABLE IF NOT EXISTS Lance (
    id_lance INTEGER PRIMARY KEY AUTOINCREMENT,
    id_leilao INTEGER,
    id_cliente INTEGER,
    valor REAL NOT NULL,
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT CHECK(status IN ('válido', 'inválido', 'vencedor')) DEFAULT 'válido',
    FOREIGN KEY (id_leilao) REFERENCES Leilao(id_leilao),
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
);

-- Tabela de Histórico de Leilões
CREATE TABLE IF NOT EXISTS Historico_Leilao (
    id_historico INTEGER PRIMARY KEY AUTOINCREMENT,
    id_leilao INTEGER,
    id_carro INTEGER,
    id_cliente_vencedor INTEGER,
    valor_final REAL,
    total_lances INTEGER,
    data_encerramento DATETIME,
    status_final TEXT CHECK(status_final IN ('vendido', 'não vendido', 'cancelado')),
    FOREIGN KEY (id_leilao) REFERENCES Leilao(id_leilao),
    FOREIGN KEY (id_carro) REFERENCES Carro(id_carro),
    FOREIGN KEY (id_cliente_vencedor) REFERENCES Cliente(id_cliente)
);

-- Tabela de Pagamentos
CREATE TABLE IF NOT EXISTS Pagamento (
    id_pagamento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_historico INTEGER,
    id_cliente INTEGER,
    valor REAL NOT NULL,
    metodo_pagamento TEXT CHECK(metodo_pagamento IN ('cartão', 'boleto', 'pix', 'transferência')) NOT NULL,
    status TEXT CHECK(status IN ('pendente', 'aprovado', 'recusado', 'estornado')) DEFAULT 'pendente',
    data_pagamento DATETIME,
    codigo_transacao TEXT,
    FOREIGN KEY (id_historico) REFERENCES Historico_Leilao(id_historico),
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente)
);

-- Tabela de Avaliações
CREATE TABLE IF NOT EXISTS Avaliacao (
    id_avaliacao INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER,
    id_leilao INTEGER,
    nota INTEGER CHECK (nota BETWEEN 1 AND 5),
    comentario TEXT,
    data_avaliacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_cliente) REFERENCES Cliente(id_cliente),
    FOREIGN KEY (id_leilao) REFERENCES Leilao(id_leilao)
);

-- Tabela de Notificações
CREATE TABLE IF NOT EXISTS Notificacao (
    id_notificacao INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER,
    titulo TEXT NOT NULL,
    mensagem TEXT NOT NULL,
    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    lida INTEGER DEFAULT 0,
    tipo TEXT CHECK(tipo IN ('lance', 'leilao', 'pagamento', 'sistema')) NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES Usuario(id_usuario)
);

-- Índices para otimização de consultas
CREATE INDEX IF NOT EXISTS idx_carro_categoria ON Carro(id_categoria);
CREATE INDEX IF NOT EXISTS idx_leilao_status ON Leilao(status);
CREATE INDEX IF NOT EXISTS idx_lance_leilao ON Lance(id_leilao);
CREATE INDEX IF NOT EXISTS idx_lance_cliente ON Lance(id_cliente);
CREATE INDEX IF NOT EXISTS idx_usuario_email ON Usuario(email);

-- Inserção de dados iniciais para categorias
INSERT OR IGNORE INTO Categoria (id_categoria, nome, descricao) VALUES
(1, 'Clássico', 'Carros clássicos e antigos com valor histórico'),
(2, 'Esportivo', 'Carros de alto desempenho e design esportivo'),
(3, 'Moderno', 'Carros modernos com tecnologia avançada'),
(4, 'Luxo', 'Carros de luxo com acabamento premium'),
(5, 'SUV', 'Veículos utilitários esportivos'),
(6, 'Sedan', 'Carros de quatro portas com porta-malas separado'),
(7, 'Hatch', 'Carros compactos com porta-malas integrado'),
(8, 'Popular', 'Carros de fácil acesso'),
(9, 'Pickup', 'Caminhonetes para trabalho e lazer');
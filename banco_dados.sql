-- Criação do banco de dados
CREATE DATABASE IF NOT EXISTS almoxarifado;

-- Seleciona o banco de dados para uso
USE almoxarifado;

-- Criação do usuário
CREATE USER IF NOT EXISTS 'tcc'@'localhost' IDENTIFIED BY '123';
GRANT ALL PRIVILEGES ON almoxarifado.* TO 'tcc'@'localhost';
FLUSH PRIVILEGES;

-- Criação da tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sn VARCHAR(100) NOT NULL UNIQUE,
    nome VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    senha VARCHAR(100),
    cargo VARCHAR(100)
);

-- Criação da tabela de materiais com a substituição do estoque_maximo por codigo_produto
CREATE TABLE IF NOT EXISTS materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descricao VARCHAR(255),
    categoria ENUM(
        'consumiveis', 
        'ferramentas', 
        'equipamentos', 
        'materiais_de_escritorio', 
        'limpeza', 
        'tecnologia', 
        'marcenaria', 
        'papelaria', 
        'seguranca'
    ) NOT NULL,
    localizacao VARCHAR(100),
    estoque_minimo INT,
    codigo_produto INT
);

-- Criação da tabela de estoque
CREATE TABLE IF NOT EXISTS estoque (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT,
    quantidade INT NOT NULL,
    data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_movimentacao ENUM('entrada', 'saida') NOT NULL,
    usuario_id INT,
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (usuario_id) REFERENCES users(id)
);

-- Criação da tabela de requisições
CREATE TABLE IF NOT EXISTS requisicoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT,
    usuario_id INT,
    quantidade INT NOT NULL,
    data_requisicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Solicitado', 'Disponivel para retirada', 'Aguardando reposição', 'Retirado') DEFAULT 'Solicitado',
    data_entrega TIMESTAMP NULL,
    observacao VARCHAR(255),
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (usuario_id) REFERENCES users(id)
);

-- Criação da tabela de histórico de requisições
CREATE TABLE IF NOT EXISTS requisicoes_historico (
    id INT PRIMARY KEY AUTO_INCREMENT,
    requisicao_id INT NOT NULL,
    data_aprovacao DATETIME NOT NULL,
    FOREIGN KEY (requisicao_id) REFERENCES requisicoes(id)
);

-- Criação da tabela de lembretes
CREATE TABLE IF NOT EXISTS lembretes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    destinatario INT,  -- Chave estrangeira para a tabela de usuários
    descricao TEXT,
    data_lembrete DATE,
    FOREIGN KEY (destinatario) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS senha_resetada (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Inserção de exemplo para tabela de usuários
INSERT INTO users (sn, nome, email, senha, cargo) VALUES 
('11', 'Admin', 'admin@example.com', 'senha123', 'admin'),
('22', 'Funcionario', 'funcionario@example.com', 'senha123', 'funcionario'),
('33', 'Octavio', 'octavio@gmail.com', 'senha123', 'almoxarifado');

-- Inserção de exemplo para tabela de materiais com código_produto no lugar de estoque_maximo
INSERT INTO materials (descricao, categoria, localizacao, estoque_minimo, codigo_produto) VALUES 
('Parafuso', 'consumiveis', 'Prateleira A1', 50, 500),
('Martelo', 'ferramentas', 'Prateleira B1', 10, 50),
('PASTA ARQUIVO', 'consumiveis', 'Prateleira A1', 10, 100),
('APAGADOR', 'consumiveis', 'Prateleira A1', 10, 100),
('CORRETIVO EM FITA', 'consumiveis', 'Prateleira A2', 10, 100),
('BARBANTE 100% ALGODÃO', 'consumiveis', 'Prateleira A2', 10, 100),
('FITA CREPE 18X50M', 'consumiveis', 'Prateleira B1', 10, 100),
('FITA CREPE 24X50M', 'consumiveis', 'Prateleira B1', 10, 100),
('FITA CREPE 48X50M', 'consumiveis', 'Prateleira B2', 10, 100),
('FITA LARGA 48X45M', 'consumiveis', 'Prateleira B2', 10, 100),
('FITA LARGA 45X45M', 'consumiveis', 'Prateleira B3', 10, 100),
('FITA DUPLA FACE', 'consumiveis', 'Prateleira B3', 10, 100),
('DUREX 12X30M', 'consumiveis', 'Prateleira C1', 10, 100),
('DVD+R', 'consumiveis', 'Prateleira C1', 10, 100),
('CD-R', 'consumiveis', 'Prateleira C2', 10, 100),
('ESTILETE', 'ferramentas', 'Prateleira C2', 5, 50),
('PEN DRIVE 16G', 'equipamentos', 'Prateleira D1', 10, 50),
('CANETA HIDROGRÁFICA', 'consumiveis', 'Prateleira D1', 10, 100),
('PLASTICO A4 COM FUROS', 'consumiveis', 'Prateleira D2', 10, 100),
('CADERNO UNIVERSITÁRIO 1 MATÉRIA', 'consumiveis', 'Prateleira D2', 10, 100),
('PASTA EM L', 'consumiveis', 'Prateleira E1', 10, 100),
('FELTRO PARA APAGADOR', 'consumiveis', 'Prateleira E1', 10, 100),
('GIZ BRANCO', 'consumiveis', 'Prateleira E2', 10, 100),
('GIZ COLORIDO', 'consumiveis', 'Prateleira E2', 10, 100),
('LÁPIS DE COR', 'consumiveis', 'Prateleira E3', 10, 100),
('FITA MÁGICA', 'consumiveis', 'Prateleira E3', 10, 100),
('PONTA DE CANETÃO', 'consumiveis', 'Prateleira F1', 10, 100),
('APONTADOR COM DEPÓSITO', 'ferramentas', 'Prateleira F1', 5, 50),
('APONTADOR SEM DEPÓSITO', 'ferramentas', 'Prateleira F2', 5, 50),
('COLA BASTÃO', 'consumiveis', 'Prateleira F2', 10, 100),
('COLA BRANCA LÍQUIDA', 'consumiveis', 'Prateleira F3', 10, 100),
('GRAMPOS 26X06', 'consumiveis', 'Prateleira F3', 10, 100),
('LÁPIS PRETO', 'consumiveis', 'Prateleira G1', 10, 100),
('CANETA BIC AZUL', 'consumiveis', 'Prateleira G1', 10, 100),
('CANETA BIC PRETA', 'consumiveis', 'Prateleira G2', 10, 100),
('CANETA BIC VERMELHA', 'consumiveis', 'Prateleira G2', 10, 100),
('MARCA TEXTO LARANJA', 'consumiveis', 'Prateleira G3', 10, 100),
('MARCA TEXTO AMARELO', 'consumiveis', 'Prateleira G3', 10, 100),
('MARCA TEXTO ROSA', 'consumiveis', 'Prateleira H1', 10, 100),
('MARCA TEXTO ROXO', 'consumiveis', 'Prateleira H1', 10, 100),
('MARCA TEXTO AZUL', 'consumiveis', 'Prateleira H2', 10, 100),
('MARCA TEXTO VERDE', 'consumiveis', 'Prateleira H2', 10, 100),
('MARCADOR PARA RETRO PROJETOR - AZUL', 'consumiveis', 'Prateleira H3', 10, 100),
('MARCADOR PARA RETRO PROJETOR - PRETO', 'consumiveis', 'Prateleira H3', 10, 100);

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

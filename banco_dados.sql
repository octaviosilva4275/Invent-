-- Criação do banco de dados
CREATE DATABASE almoxarifado;

-- Seleciona o banco de dados para uso
USE almoxarifado;


CREATE USER 'tcc'@'localhost' IDENTIFIED BY '123';
GRANT ALL PRIVILEGES ON almoxarifado.* TO 'tcc'@'localhost';
FLUSH PRIVILEGES;


CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sn VARCHAR(100) NOT NULL UNIQUE,
    nome VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    senha VARCHAR(100),
    cargo VARCHAR(100)
);


-- Tabela de materiais sem fornecedor
CREATE TABLE materials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    descricao TEXT NOT NULL,
    categoria ENUM('consumiveis', 'ferramentas', 'equipamentos') NOT NULL,
    localizacao VARCHAR(100),
    estoque_minimo INT,
    estoque_maximo INT
);




-- Tabela de estoque
CREATE TABLE estoque (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT,
    quantidade INT NOT NULL,
    data_movimentacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_movimentacao ENUM('entrada', 'saida') NOT NULL,
    usuario_id INT,
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (usuario_id) REFERENCES users(id)
);

-- Tabela de requisições
CREATE TABLE requisicoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    material_id INT,
    usuario_id INT,
    quantidade INT NOT NULL,
    data_requisicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pendente', 'aprovada', 'rejeitada') DEFAULT 'pendente',
    data_entrega TIMESTAMP NULL,
    observacao VARCHAR(255),
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (usuario_id) REFERENCES users(id)
);

CREATE TABLE requisicoes_historico (
    id INT PRIMARY KEY AUTO_INCREMENT,
    requisicao_id INT NOT NULL,
    data_aprovacao DATETIME NOT NULL,
    FOREIGN KEY (requisicao_id) REFERENCES requisicoes(id)
);

CREATE TABLE lembretes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    destinatario VARCHAR(100),  -- Ou uma chave estrangeira para a tabela de usuários
    descricao TEXT,
    data_lembrete DATE
);

INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) 
VALUES (1, -5, 'saida', 2);  -- Assumindo que o usuário 2 fez a saída

INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) 
VALUES (2, 30, 'entrada', 1); 

INSERT INTO lembretes (destinatario, descricao, data_lembrete) 
VALUES ('João Silva', 'Reunião de equipe às 14h', '2024-08-03'); 

-- Inserção de exemplo para tabela de usuários
INSERT INTO users (sn, nome, email, senha, cargo) VALUES 
('11', 'Admin', 'admin@example.com', 'senha123', 'admin'),
('22', 'Funcionario', 'funcionario@example.com', 'senha123', 'funcionario');

-- Inserção de exemplo para tabela de materiais sem fornecedor
INSERT INTO materials (descricao, categoria, localizacao, estoque_minimo, estoque_maximo) VALUES 
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
('MARCADOR PARA RETRO PROJETOR - VERMELHO', 'consumiveis', 'Prateleira H3', 10, 100),
('MARCADOR PARA RETRO PROJETOR - VERDE', 'consumiveis', 'Prateleira I1', 10, 100),
('MARCADOR PARA RETRO PROJETOR - PRETO', 'consumiveis', 'Prateleira I1', 10, 100),
('MARCADOR PERMANENTE - AZUL', 'consumiveis', 'Prateleira I2', 10, 100),
('GRAFITE 0,9', 'consumiveis', 'Prateleira I2', 10, 100),
('MOLHA DEDO', 'consumiveis', 'Prateleira J1', 10, 100),
('BORRACHA BRANCA', 'consumiveis', 'Prateleira J1', 10, 100),
('PERCEVEJO', 'consumiveis', 'Prateleira J2', 10, 100),
('CLIPES GRANDE 0.8', 'consumiveis', 'Prateleira J2', 10, 100),
('CLIPES GRANDE 0.2', 'consumiveis', 'Prateleira K1', 10, 100),
('EXTRATOR', 'ferramentas', 'Prateleira K1', 5, 50),
('ELÁSTICO DE BORRACHA', 'consumiveis', 'Prateleira K2', 10, 100),
('POST-IT 76X102', 'consumiveis', 'Prateleira K2', 10, 100),
('POST-IT 38X50', 'consumiveis', 'Prateleira L1', 10, 100),
('PELÍCULA DE ADESIVO', 'consumiveis', 'Prateleira L1', 10, 100),
('PRANCHETA', 'ferramentas', 'Prateleira L2', 10, 50),
('TESOURA', 'ferramentas', 'Prateleira L2', 10, 50),
('PRESILHA PARA PASTA', 'consumiveis', 'Prateleira M1', 10, 100),
('GRAMPEADOR GRANDE', 'ferramentas', 'Prateleira M1', 5, 50),
('GRAMPEADOR PROFISSIONAL', 'ferramentas', 'Prateleira M2', 5, 50),
('SUPORTE PARA DUREX PEQUENO', 'ferramentas', 'Prateleira M2', 10, 50),
('LÍQUIDO PARA LIMPAR QUADRO BRANCO', 'consumiveis', 'Prateleira N1', 10, 100),
('GRAMPO GALVANIZADO', 'consumiveis', 'Prateleira N1', 10, 100),
('CANETÃO AZUL', 'consumiveis', 'Prateleira N2', 10, 100),
('CANETÃO PRETO', 'consumiveis', 'Prateleira N2', 10, 100),
('CANETÃO VERMELHO', 'consumiveis', 'Prateleira O1', 10, 100),
('RECARGA PARA CANETÃO PRETO', 'consumiveis', 'Prateleira O1', 10, 100),
('RECARGA PARA CANETÃO AZUL', 'consumiveis', 'Prateleira O2', 10, 100),
('RECARGA PARA CANETÃO VERMELHO', 'consumiveis', 'Prateleira O2', 10, 100),
('ALMOFADA PARA CARIMBO', 'consumiveis', 'Prateleira P1', 10, 100),
('PASTA DE A-Z', 'consumiveis', 'Prateleira P1', 10, 100),
('PASTA CATÁLOGO', 'consumiveis', 'Prateleira P2', 10, 100),
('PASTA DE PAPELÃO', 'consumiveis', 'Prateleira P2', 10, 100),
('PASTA GRAMPO TRILHO', 'consumiveis', 'Prateleira P3', 10, 100),
('LIVRO ATA', 'consumiveis', 'Prateleira P3', 10, 100),
('PASTA COM CANALETA', 'consumiveis', 'Prateleira Q1', 10, 100),
('PASTA EM L', 'consumiveis', 'Prateleira Q1', 10, 100),
('ETIQUETA AUTOADESIVA 215,09X279,04MM', 'consumiveis', 'Prateleira Q2', 10, 100),
('PAPEL VERGÊ VERDE', 'consumiveis', 'Prateleira Q2', 10, 100),
('PAPEL VERGÊ MADRE PÉROLA', 'consumiveis', 'Prateleira Q3', 10, 100),
('ETIQUETA AUTOADESIVA 33,9 X 101,6MM', 'consumiveis', 'Prateleira Q3', 10, 100),
('ETIQUETA AUTOADESIVA 101,6 X 25,4MM', 'consumiveis', 'Prateleira R1', 10, 100),
('ETIQUETA AUTOADESIVA 25,4X101,6MM', 'consumiveis', 'Prateleira R1', 10, 100);

-- Inserção de exemplo para tabela de estoque
INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) VALUES 
(1, 100, 'entrada', 1),
(2, 20, 'entrada', 1);

-- Inserção de exemplo para tabela de requisições
INSERT INTO requisicoes (material_id, usuario_id, quantidade, status) VALUES 
(1, 2, 10, 'aprovada'),
(2, 2, 5, 'pendente');




INSERT INTO estoque (material_id, quantidade, tipo_movimentacao, usuario_id) VALUES
(1, 9, 'entrada', 1),        -- Parafuso (4 + 5)
(2, 10, 'entrada', 1),       -- Martelo (5 + 5)
(3, 16, 'entrada', 1),      -- PASTA ARQUIVO (11 + 5)
(4, 5, 'entrada', 1),        -- APAGADOR (NULL + 5 -> 5)
(5, 5, 'entrada', 1),        -- CORRETIVO EM FITA (NULL + 5 -> 5)
(6, 5, 'entrada', 1),        -- BARBANTE 100% ALGODÃO (NULL + 5 -> 5)
(7, 5, 'entrada', 1),        -- FITA CREPE 18X50M (NULL + 5 -> 5)
(8, 5, 'entrada', 1),        -- FITA CREPE 24X50M (NULL + 5 -> 5)
(9, 5, 'entrada', 1),        -- FITA CREPE 48X50M (NULL + 5 -> 5)
(10, 5, 'entrada', 1),       -- FITA LARGA 48X45M (NULL + 5 -> 5)
(11, 5, 'entrada', 1),       -- FITA LARGA 45X45M (NULL + 5 -> 5)
(12, 5, 'entrada', 1),       -- FITA DUPLA FACE (NULL + 5 -> 5)
(13, 5, 'entrada', 1),       -- DUREX 12X30M (NULL + 5 -> 5)
(14, 5, 'entrada', 1),       -- DVD+R (NULL + 5 -> 5)
(15, 5, 'entrada', 1),       -- CD-R (NULL + 5 -> 5)
(16, 5, 'entrada', 1),       -- ESTILETE (NULL + 5 -> 5)
(17, 5, 'entrada', 1),       -- PEN DRIVE 16G (NULL + 5 -> 5)
(18, 5, 'entrada', 1),       -- CANETA HIDROGRÁFICA (NULL + 5 -> 5)
(19, 5, 'entrada', 1),       -- PLASTICO A4 COM FUROS (NULL + 5 -> 5)
(20, 5, 'entrada', 1),       -- CADERNO UNIVERSITÁRIO 1 MATÉRIA (NULL + 5 -> 5)
(21, 5, 'entrada', 1),       -- PASTA EM L (NULL + 5 -> 5)
(22, 5, 'entrada', 1),       -- FELTRO PARA APAGADOR (NULL + 5 -> 5)
(23, 5, 'entrada', 1),       -- GIZ BRANCO (NULL + 5 -> 5)
(24, 5, 'entrada', 1),       -- GIZ COLORIDO (NULL + 5 -> 5)
(25, 5, 'entrada', 1),       -- LÁPIS DE COR (NULL + 5 -> 5)
(26, 5, 'entrada', 1),       -- FITA MÁGICA (NULL + 5 -> 5)
(27, 5, 'entrada', 1),       -- PONTA DE CANETÃO (NULL + 5 -> 5)
(28, 5, 'entrada', 1),       -- APONTADOR COM DEPÓSITO (NULL + 5 -> 5)
(29, 5, 'entrada', 1),       -- APONTADOR SEM DEPÓSITO (NULL + 5 -> 5)
(30, 5, 'entrada', 1),       -- COLA BASTÃO (NULL + 5 -> 5)
(31, 5, 'entrada', 1),       -- COLA BRANCA LÍQUIDA (NULL + 5 -> 5)
(32, 5, 'entrada', 1),       -- GRAMPOS 26X06 (NULL + 5 -> 5)
(33, 5, 'entrada', 1),       -- LÁPIS PRETO (NULL + 5 -> 5)
(34, 5, 'entrada', 1),       -- CANETA BIC AZUL (NULL + 5 -> 5)
(35, 5, 'entrada', 1),       -- CANETA BIC PRETA (NULL + 5 -> 5)
(36, 5, 'entrada', 1),       -- CANETA BIC VERMELHA (NULL + 5 -> 5)
(37, 5, 'entrada', 1),       -- MARCA TEXTO LARANJA (NULL + 5 -> 5)
(38, 5, 'entrada', 1),       -- MARCA TEXTO AMARELO (NULL + 5 -> 5)
(39, 5, 'entrada', 1),       -- MARCA TEXTO ROSA (NULL + 5 -> 5)
(40, 5, 'entrada', 1),       -- MARCA TEXTO ROXO (NULL + 5 -> 5)
(41, 5, 'entrada', 1),       -- MARCA TEXTO AZUL (NULL + 5 -> 5)
(42, 5, 'entrada', 1),       -- MARCA TEXTO VERDE (NULL + 5 -> 5)
(43, 5, 'entrada', 1),       -- MARCADOR PARA RETRO PROJETOR - AZUL (NULL + 5 -> 5)
(44, 5, 'entrada', 1),       -- MARCADOR PARA RETRO PROJETOR - VERMELHO (NULL + 5 -> 5)
(45, 5, 'entrada', 1),       -- MARCADOR PARA RETRO PROJETOR - VERDE (NULL + 5 -> 5)
(46, 5, 'entrada', 1),       -- MARCADOR PARA RETRO PROJETOR - PRETO (NULL + 5 -> 5)
(47, 5, 'entrada', 1),       -- MARCADOR PERMANENTE - AZUL (NULL + 5 -> 5)
(48, 5, 'entrada', 1),       -- GRAFITE 0,9 (NULL + 5 -> 5)
(49, 5, 'entrada', 1),       -- MOLHA DEDO (NULL + 5 -> 5)
(50, 5, 'entrada', 1),       -- BORRACHA BRANCA (NULL + 5 -> 5)
(51, 5, 'entrada', 1),       -- PERCEVEJO (NULL + 5 -> 5)
(52, 5, 'entrada', 1),       -- CLIPS GRANDE 0.8 (NULL + 5 -> 5)
(53, 5, 'entrada', 1),       -- CLIPS GRANDE 0.2 (NULL + 5 -> 5)
(54, 5, 'entrada', 1),       -- EXTRATOR (NULL + 5 -> 5)
(55, 5, 'entrada', 1),       -- ELÁSTICO DE BORRACHA (NULL + 5 -> 5)
(56, 5, 'entrada', 1),       -- POST-IT 76X102 (NULL + 5 -> 5)
(57, 5, 'entrada', 1),       -- POST-IT 38X50 (NULL + 5 -> 5)
(58, 5, 'entrada', 1),       -- PELÍCULA DE ADESIVO (NULL + 5 -> 5)
(59, 5, 'entrada', 1),       -- PRANCHETA (NULL + 5 -> 5)
(60, 5, 'entrada', 1),       -- TESOURA (NULL + 5 -> 5)
(61, 5, 'entrada', 1),       -- PRESILHA PARA PASTA (NULL + 5 -> 5)
(62, 5, 'entrada', 1),       -- GRAMPEADOR GRANDE (NULL + 5 -> 5)
(63, 5, 'entrada', 1),       -- GRAMPEADOR PROFISSIONAL (NULL + 5 -> 5)
(64, 5, 'entrada', 1),       -- SUPORTE PARA DUREX PEQUENO (NULL + 5 -> 5)
(65, 5, 'entrada', 1),       -- LÍQUIDO PARA LIMPAR QUADRO BRANCO (NULL + 5 -> 5)
(66, 5, 'entrada', 1),       -- GRAMPO GALVANIZADO (NULL + 5 -> 5)
(67, 5, 'entrada', 1),       -- CANETÃO AZUL (NULL + 5 -> 5)
(68, 5, 'entrada', 1),       -- CANETÃO PRETO (NULL + 5 -> 5)
(69, 5, 'entrada', 1),       -- CANETÃO VERMELHO (NULL + 5 -> 5)
(70, 5, 'entrada', 1),       -- RECARGA PARA CANETÃO PRETO (NULL + 5 -> 5)
(71, 5, 'entrada', 1),       -- RECARGA PARA CANETÃO AZUL (NULL + 5 -> 5)
(72, 5, 'entrada', 1),       -- RECARGA PARA CANETÃO VERMELHO (NULL + 5 -> 5)
(73, 5, 'entrada', 1),       -- ALMOFADA PARA CARIMBO (NULL + 5 -> 5)
(74, 5, 'entrada', 1),       -- PASTA DE A-Z (NULL + 5 -> 5)
(75, 5, 'entrada', 1),       -- PASTA CATÁLOGO (NULL + 5 -> 5)
(76, 5, 'entrada', 1),       -- PASTA DE PAPELÃO (NULL + 5 -> 5)
(77, 5, 'entrada', 1),       -- PASTA GRAMPO TRILHO (NULL + 5 -> 5)
(78, 5, 'entrada', 1);       -- LIVRO ATA (NULL + 5 -> 5)
(79, 5, 'entrada', 1),       -- PASTA COM CANALETA (NULL + 5 -> 5)
(80, 5, 'entrada', 1),       -- PASTA EM L (NULL + 5 -> 5)
(81, 5, 'entrada', 1),       -- ETIQUETA AUTOADESIVA 215,09X279,04MM (NULL + 5 -> 5)
(82, 5, 'entrada', 1),       -- PAPEL VERGÊ VERDE (NULL + 5 -> 5)
(83, 5, 'entrada', 1),       -- PAPEL VERGÊ MADRE PÉROLA (NULL + 5 -> 5)
(84, 5, 'entrada', 1),       -- ETIQUETA AUTOADESIVA 33,9 X 101,6MM (NULL + 5 -> 5)
(85, 5, 'entrada', 1),       -- ETIQUETA AUTOADESIVA 101,6 X 25,4MM (NULL + 5 -> 5)
(86, 5, 'entrada', 1);       -- ETIQUETA AUTOADESIVA 25,4X101,6MM (NULL + 5 -> 5)
 

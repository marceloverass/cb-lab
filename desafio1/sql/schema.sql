CREATE TABLE Restaurantes (
    restaurante_id INT IDENTITY(1,1) PRIMARY KEY,
    loc_ref NVARCHAR(255) NOT NULL
);
GO

CREATE TABLE Funcionarios (
    funcionario_id INT IDENTITY(1,1) PRIMARY KEY,
    numero_funcionario INT NOT NULL,
    nome_completo NVARCHAR(255),
    cargo NVARCHAR(100)
);
GO

CREATE TABLE Formas_Pagamento_Catalogo (
    forma_pagamento_id INT IDENTITY(1,1) PRIMARY KEY,
    nome NVARCHAR(100) NOT NULL,
    ativo BIT NOT NULL DEFAULT 1,
    cobra_taxa BIT NOT NULL DEFAULT 0
);
GO

CREATE TABLE Erros_Catalogo (
    erro_id INT IDENTITY(1,1) PRIMARY KEY,
    codigo_erro INT UNIQUE NOT NULL,
    descricao_curta NVARCHAR(100),
    mensagem_detalhada NVARCHAR(500),
    tipo_erro NVARCHAR(50)
);
GO

CREATE TABLE Pedidos (
    guest_check_id BIGINT PRIMARY KEY,
    restaurante_id_fk INT NOT NULL,
    funcionario_id_fk INT NOT NULL,
    numero_pedido INT,
    data_negocio_aberto DATE,
    data_abertura_utc DATETIMEOFFSET,
    data_fechamento_utc DATETIMEOFFSET,
    fechado BIT NOT NULL DEFAULT 0,
    total_pedido DECIMAL(10, 2),
    total_desconto DECIMAL(10, 2),
    total_pago DECIMAL(10, 2),
    numero_mesa NVARCHAR(50)
);
GO

CREATE TABLE Impostos_Pedidos (
    imposto_pedido_id INT IDENTITY(1,1) PRIMARY KEY,
    guest_check_id_fk BIGINT NOT NULL,
    numero_imposto INT,
    total_venda_tributavel DECIMAL(10, 2),
    total_imposto_cobrado DECIMAL(10, 2),
    taxa_imposto DECIMAL(5, 2)
);
GO

CREATE TABLE Linhas_Detalhe (
    guest_check_line_item_id BIGINT PRIMARY KEY,
    guest_check_id_fk BIGINT NOT NULL,
    numero_linha INT,
    data_detalhe_utc DATETIMEOFFSET,
    total_liquido DECIMAL(10, 2),
    quantidade DECIMAL(10, 2),
    tipo_detalhe NVARCHAR(50) NOT NULL,
    id_detalhe_especifico BIGINT NOT NULL
);
GO

CREATE TABLE Detalhe_ItemMenu (
    item_menu_detalhe_id INT IDENTITY(1,1) PRIMARY KEY,
    numero_item_menu INT,
    modificado BIT,
    imposto_incluso DECIMAL(10, 5),
    impostos_ativos NVARCHAR(255),
    nivel_preco INT
);
GO

CREATE TABLE Detalhe_Desconto (
    desconto_detalhe_id INT IDENTITY(1,1) PRIMARY KEY,
    motivo_desconto NVARCHAR(255),
    valor_desconto DECIMAL(10, 2)
);
GO

CREATE TABLE Detalhe_TaxaServico (
    taxa_servico_detalhe_id INT IDENTITY(1,1) PRIMARY KEY,
    tipo_taxa NVARCHAR(100),
    valor_taxa DECIMAL(10, 2)
);
GO

CREATE TABLE Detalhe_FormaPagamento (
    pagamento_detalhe_id INT IDENTITY(1,1) PRIMARY KEY,
    forma_pagamento_id_fk INT NOT NULL,
    valor_pago DECIMAL(10, 2)
);
GO

CREATE TABLE Detalhe_Erro (
    erro_detalhe_id INT IDENTITY(1,1) PRIMARY KEY,
    erro_id_fk INT NOT NULL,
    detalhes_adicionais NVARCHAR(MAX)
);
GO

ALTER TABLE Pedidos
ADD CONSTRAINT FK_Pedidos_Restaurantes FOREIGN KEY (restaurante_id_fk) REFERENCES Restaurantes(restaurante_id);
GO

ALTER TABLE Pedidos
ADD CONSTRAINT FK_Pedidos_Funcionarios FOREIGN KEY (funcionario_id_fk) REFERENCES Funcionarios(funcionario_id);
GO

ALTER TABLE Impostos_Pedidos
ADD CONSTRAINT FK_Impostos_Pedidos FOREIGN KEY (guest_check_id_fk) REFERENCES Pedidos(guest_check_id);
GO

ALTER TABLE Linhas_Detalhe
ADD CONSTRAINT FK_Linhas_Detalhe_Pedidos FOREIGN KEY (guest_check_id_fk) REFERENCES Pedidos(guest_check_id);
GO

ALTER TABLE Detalhe_FormaPagamento
ADD CONSTRAINT FK_Detalhe_FormaPagamento_Catalogo FOREIGN KEY (forma_pagamento_id_fk) REFERENCES Formas_Pagamento_Catalogo(forma_pagamento_id);
GO

ALTER TABLE Detalhe_Erro
ADD CONSTRAINT FK_Detalhe_Erro_Catalogo FOREIGN KEY (erro_id_fk) REFERENCES Erros_Catalogo(erro_id);
GO
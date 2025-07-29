# Desafio Engenharia de Dados CB LAB

Este projeto contém a solução para o Desafio de Engenharia de Dados do Coco Bambu(CB Lab) 2025. O objetivo é extrair dados de um arquivo JSON proveniente de um ERP de restaurante, modelar uma estrutura de banco de dados relacional robusta, criar essa estrutura em um container SQL Server e, por fim, popular o banco de dados com os dados do arquivo JSON através de um processo de ETL.

## Tecnologias Utilizadas

* **Linguagem:** Python
* **Containerização:** Docker & Docker Compose
* **Banco de Dados:** Microsoft SQL Server (rodando em Linux)
* **Análise e Documentação:** Jupyter Notebook
* **Bibliotecas Python:** `pyodbc`, `pandas`

---

## 🚀 Começando

Siga os passos abaixo para clonar, configurar e executar o projeto em seu ambiente local.

### Pré-requisitos

* Docker e Docker Compose devem estar instalados e em execução.
* Git para clonar o repositório.
* Um sistema operacional com um terminal (Linux, macOS ou WSL no Windows).

### Passo 1: Clone o Repositório

```bash
git clone [https://github.com/marceloverass/cb-lab]
cd [cb-lab]
```

### Passo 2: Inicie o Ambiente Docker

Este comando irá construir a imagem da aplicação Python e iniciar os containers da aplicação (`desafio_app`) e do banco de dados (`desafio_db`) em segundo plano.

```bash
docker compose up --build -d
```

**Importante:** Após executar o comando, aguarde de **1 a 2 minutos** para que o serviço do SQL Server seja totalmente inicializado antes de prosseguir para o próximo passo.

### Passo 3: Inicialize o Banco de Dados

Rode os comandos abaixo para se conectar ao container do SQL Server, criar o banco de dados `DesafioDB` (se ele não existir) e executar o script para criar todas as tabelas.

**3.1 - Criar o Banco de Dados (de forma segura):**
```bash
docker exec -it desafio_db /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'CocoBambuCBLAB123@@' -N -C -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DesafioDB') CREATE DATABASE DesafioDB;"
```

**3.2 - Copiar o Script do Schema para o Container:**
```bash
docker cp desafio1/sql/schema.sql desafio_db:/tmp/schema.sql
```

**3.3 - Executar o Script para Criar as Tabelas:**
```bash
docker exec -it desafio_db /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'CocoBambuCBLAB123@@' -N -C -d DesafioDB -i /tmp/schema.sql
```

Neste ponto, o ambiente está 100% configurado com a infraestrutura pronta.

### Passo 4: Executar o Processo de ETL

O processo de ETL é executado através de um script Python localizado dentro do container da aplicação. Para executá-lo, utilize o seguinte comando:

```bash
docker exec -it desafio_app python desafio1/src/etl-prod/main.py
```
---

**Para testar com novos dados:**
1.  Adicione um novo arquivo JSON (ou uma cópia do `ERP.json` com um nome diferente) na pasta `desafio1/etl-prod/input_files/`.
2.  Para facilitar, adicionei uma pasta `sample-data`, dentro da pasta `desafio1`, contendo alguns arquivos json para teste. Copie e cole os arquivos json que quiser testar na pasta `input_files`.
3.  Execute o comando de ETL abaixo.

O script irá processar todos os arquivos na pasta de entrada, inserindo novos pedidos e atualizando os existentes se um ID de pedido for repetido.

## 📖 Visualizando a Análise e Documentação

O processo de modelagem de dados foi inteiramente documentado em um Jupyter Notebook. Para visualizá-lo:

**1. Inicie o servidor JupyterLab:**
```bash
docker exec -it desafio_app jupyter lab --ip=0.0.0.0 --allow-root --port=8888 --no-browser --notebook-dir=/app/notebooks
```

**2. Acesse no Navegador:**
Copie o link que aparecerá no terminal (incluindo o `token`) e cole no seu navegador.

**3. Visualize no próprio GitHub:**
Os notebooks com toda a análise estão na pasta `notebooks` e os arquivos têm a extensão `ipynb`.
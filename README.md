# Desafio de Engenharia de Dados

Este repositório contém a solução completa para os desafios de Engenharia de Dados propostos. O projeto implementa um pipeline de dados de ponta a ponta, desde a ingestão de dados de APIs até a sua disponibilização em um Data Warehouse modelado para análises de negócio.

## Arquitetura da Solução

A solução foi projetada utilizando a **Arquitetura Medallion**, um padrão moderno que organiza os dados em três camadas lógicas de qualidade, garantindo robustez, rastreabilidade e flexibilidade ao fluxo de dados.

Todo o ambiente é 100% containerizado com Docker para garantir a total reprodutibilidade.

## Tecnologias Utilizadas

* **Linguagem:** Python
* **Bibliotecas:** Pandas, PyArrow, PyODBC
* **Containerização:** Docker & Docker Compose
* **Banco de Dados:** Microsoft SQL Server
* **Documentação:** Jupyter Notebook, Kanban

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

* Docker e Docker Compose devem estar instalados e em execução.
* Git para clonar o repositório.

### Passo 1: Clone o Repositório

```bash
git clone [https://github.com/marceloverass/cb-lab]
cd [cb-lab]
```

### Passo 2: Inicie o Ambiente Docker

Este comando utiliza os arquivos de configuração na pasta `docker/` para construir a imagem da aplicação Python e iniciar os containers da aplicação (`desafio_app`) e do banco de dados (`desafio_db`).

```bash
docker compose -f docker/docker-compose.yml up --build -d
```
**Importante:** Após executar o comando, aguarde de **1 a 2 minutos** para que o serviço do SQL Server seja totalmente inicializado antes de prosseguir.

### Passo 3: Execute o Pipeline de Dados Completo

Os comandos abaixo devem ser executados em sequência. Eles irão inicializar o banco de dados (se necessário) e executar todo o fluxo de dados através das camadas Bronze, Silver e Gold.

**3.1 - Setup do Banco de Dados (só precisa rodar uma vez):**
```bash
# Cria o Banco de Dados
docker exec -it desafio_db /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'CocoBambuCBLAB123@@' -N -C -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DesafioDB') CREATE DATABASE DesafioDB;"

# Copia e executa o script para criar as tabelas
docker cp desafio1/sql/schema.sql desafio_db:/tmp/schema.sql
docker exec -it desafio_db /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'CocoBambuCBLAB123@@' -N -C -d DesafioDB -i /tmp/schema.sql
```

**3.2 - Execução do Pipeline de Dados:**
```bash
# Etapa 1: Ingestão da API para a camada Bronze
docker exec -it desafio_app python desafio2/src/ingestao_api.py

# Etapa 2: Transformação de Bronze para Silver
docker exec -it desafio_app python desafio1/src/etl-prod/transform_silver.py

# Etapa 3: Carga de Silver para Gold (Data Warehouse)
docker exec -it desafio_app python desafio1/src/etl-prod/main.py
```

Após a execução, o Data Warehouse estará populado e pronto para ser consultado.

---
## 📄 Visualizando a Documentação e Análise

Todo o processo de design e modelagem foi documentado em Jupyter Notebooks.

**1. Inicie o servidor JupyterLab:**
```bash
# Entra no terminal do container da aplicação
docker compose -f docker/docker-compose.yml exec app bash

# Dentro do container, executa o JupyterLab
jupyter lab --ip=0.0.0.0 --allow-root --port=8888 --no-browser --notebook-dir=/app/docs/notebooks
```

**2. Acesse no Navegador:**
Copie o link que aparecerá no terminal (incluindo o `token`) e cole no seu navegador.

**3. Documentação Adicional:**
* **Gestão de Tarefas:** O progresso do projeto foi acompanhado através do arquivo `docs/KANBAN.md`.
* **Diagramas de Modelo:** Os diagramas MER e DER estão localizados na pasta `docs/`.
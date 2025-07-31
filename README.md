# Desafio Engenharia de Dados

## Resolução dos Desafios

Para facilitar a avaliação, as soluções para cada um dos desafios foram documentadas em Jupyter Notebooks separados. Cada notebook contém a análise detalhada e as respostas para as questões propostas.

* **[📄 Notebook da Solução do Desafio 1](https://github.com/marceloverass/cb-lab/blob/main/docs/notebooks/desafio1.ipynb)**
* **[📄 Notebook da Solução do Desafio 2](https://github.com/marceloverass/cb-lab/blob/main/docs/notebooks/desafio2.ipynb)**

## Descrição

Este projeto implementa um pipeline de dados completo que ingere dados de uma fonte externa (API), processa-os através de múltiplas camadas (Bronze, Silver e Gold) e os armazena em um Data Warehouse no SQL Server. Todo o ambiente, incluindo a aplicação Python e o banco de dados, é orquestrado com Docker.

O objetivo é demonstrar habilidades em engenharia de dados, modelagem e arquitetura de dados, ETL, automação de processos e organização de um ambiente de desenvolvimento reproduzível.

## Tecnologias Utilizadas

* **Linguagem:** Python 3.10
* **Banco de Dados:** Microsoft SQL Server
* **Conteinerização:** Docker & Docker Compose
* **Bibliotecas Principais:**
    * Pandas
    * SQLAlchemy
    * PyODBC

## Pré-requisitos

Antes de começar, garanta que você tenha as seguintes ferramentas instaladas em sua máquina:

* [Git](https://git-scm.com/)
* [Docker](https://www.docker.com/products/docker-desktop/)
* [Docker Compose](https://docs.docker.com/compose/install/)

## Como Executar o Projeto

Siga os passos abaixo na ordem correta. Cada comando foi preparado para ser copiado e colado diretamente no seu terminal.

### 1. Clonar o Repositório

Primeiro, clone este repositório para a sua máquina local e navegue até a pasta do projeto.

```bash
# Clone o projeto
git clone https://github.com/marceloverass/cb-lab

# Entre na pasta do projeto
cd cb-lab
```

### 2. Iniciar os Contêineres

Este comando irá construir as imagens Docker e iniciar os serviços da aplicação e do banco de dados em segundo plano (`-d`).

```bash
docker compose up --build -d
```

Após a execução, verifique se os dois contêineres (`desafio_app` e `desafio_db`) estão em execução e saudáveis:

```bash
# Deve listar os dois contêineres com o status "Up"
docker ps
```

### 3. Configurar o Banco de Dados

Os comandos a seguir preparam o banco de dados `DesafioDB` e criam as tabelas necessárias.

**3.1. Criar o Banco de Dados**
Este comando executa um script SQL dentro do contêiner do banco de dados para criar a base `DesafioDB`, caso ela não exista.

```bash
docker exec -it desafio_db /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'CocoBambuCBLAB123@@' -N -C -Q "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'DesafioDB') CREATE DATABASE DesafioDB;"
```

**3.2. Criar as Tabelas**
Agora, copiamos o arquivo `schema.sql` para dentro do contêiner e o executamos para criar a estrutura de tabelas.

```bash
# 1. Copia o arquivo de schema para o contêiner
docker cp desafio1/sql/schema.sql desafio_db:/tmp/schema.sql
```

```bash
# 2. Executa o script para criar as tabelas dentro do banco DesafioDB
docker exec -it desafio_db /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'CocoBambuCBLAB123@@' -N -C -d DesafioDB -i /tmp/schema.sql
```

### 4. Executar o Pipeline de Dados

Com o ambiente pronto, execute cada etapa do pipeline de dados. Os scripts Python serão executados dentro do contêiner da aplicação.

**4.1. Etapa 1: Ingestão da API para a Camada Bronze**

```bash
docker exec -it desafio_app python desafio2/src/ingestao_api.py
```

**4.2. Etapa 2: Transformação de Bronze para Silver**

```bash
docker exec -it desafio_app python desafio1/src/etl-prod/transform_silver.py
```

**4.3. Etapa 3: Carga de Silver para Gold (Data Warehouse)**

```bash
docker exec -it desafio_app python desafio1/src/etl-prod/main.py
```

Ao final desta etapa, o processo estará completo!

### 5. Verificando o Resultado

Após a execução do pipeline, você pode verificar o resultado, testar consultas criadas como exemplo e criar suas próprias consultas:

**5.1. Acessar o Contêiner da Aplicação**

Primeiro, acesse o terminal interativo (shell) do contêiner desafio_app. Todos os comandos seguintes serão executados de dentro dele.

```bash
`docker compose exec desafio_app bash`
```

**5.2. Iniciar o Jupyter Notebook**

Execute o comando abaixo no seu terminal. Ele iniciará um servidor Jupyter dentro do contêiner da aplicação e fornecerá um link de acesso.

```bash
docker exec -it desafio_app jupyter notebook --ip=0.0.0.0 --port=8888 --allow-root --no-browser
```

**5.3. Acessar o Notebook**

O terminal exibirá uma mensagem com um link. Segure `Ctrl` e clique no link que contém `127.0.0.1:8888` ou cole-o no seu navegador. O link será parecido com este:

```
[http://127.0.0.1:8888/tree?token=SEU_TOKEN_SECRETO_AQUI](http://127.0.0.1:8888/tree?token=SEU_TOKEN_SECRETO_AQUI)
```

**5.4. Executar o Notebook**

Na interface do Jupyter, navegue até a pasta `desafio1/notebooks/` e abra o arquivo `exploracao_datawarehouse.ipynb`. Siga as instruções e execute as células do notebook para ver a análise dos dados.

### 6. Encerrar o Ambiente

Quando terminar a avaliação, você pode parar e remover todos os contêineres e redes criados pelo projeto com um único comando:

```bash
docker compose down
```

### 7 Gerenciamento do Projeto com Kanban

Para garantir a organização, o planejamento e a visibilidade do progresso durante o desenvolvimento deste projeto, utilizei um quadro Kanban.

O quadro detalha todas as etapas do projeto, desde a concepção e configuração do ambiente até a implementação de cada fase da pipeline de dados e a documentação final. Ele serve como um registro transparente do fluxo de trabalho e das tarefas concluídas.

* **[Kanban](https://github.com/marceloverass/cb-lab/blob/main/docs/KANBAN.md)**

## Autor

**[Marcelo Antonino Veras Sampaio]**

* [marceloantonino.verass@gmail.com]
* [https://www.linkedin.com/in/marceloveras/]
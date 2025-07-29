import pyodbc

def get_connection():
    """
    Cria e retorna um objeto de conexão com o banco de dados SQL Server.
    """
    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=desafio_db;"
        "DATABASE=DesafioDB;"
        "UID=sa;"
        "PWD=CocoBambuCBLAB123@@;"
        "TrustServerCertificate=yes;"
    )
    try:
        connection = pyodbc.connect(connection_string)
        print("Conexão com o SQL Server bem-sucedida!")
        return connection
    except Exception as e:
        print(f"Erro ao conectar ao SQL Server: {e}")
        return None
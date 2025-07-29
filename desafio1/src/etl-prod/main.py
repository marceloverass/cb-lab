# desafio1/etl-prod/main.py
import os # <-- CORREÇÃO AQUI
from connection import get_connection
from load_data import load_all_data
from validate_data import validate_data

def run_production_etl_pipeline(input_folder_path):
    """
    Orquestra a execução do pipeline de ETL em modo de produção (incremental).
    Processa TODOS os arquivos .json encontrados na pasta de entrada.
    """
    print("===== INICIANDO PIPELINE DE ETL EM MODO DE PRODUÇÃO =====")
    
    try:
        json_files = [f for f in os.listdir(input_folder_path) if f.endswith('.json')]
        if not json_files:
            print(f"AVISO: Nenhum arquivo .json encontrado em '{input_folder_path}'. Encerrando.")
            return
        print(f"Arquivos a serem processados: {json_files}")
    except FileNotFoundError:
        print(f"ERRO CRÍTICO: A pasta de entrada '{input_folder_path}' não foi encontrada. Encerrando.")
        return

    connection = None
    try:
        connection = get_connection()
        
        if connection:
            for file_name in json_files:
                file_path = os.path.join(input_folder_path, file_name)
                load_all_data(connection, file_path)
            
            validate_data(connection)
            
    except Exception as e:
        print(f"Ocorreu um erro fatal no orquestrador principal: {e}")
    finally:
        if connection:
            connection.close()
            print("\nConexão com o banco de dados fechada.")
            
    print("===== PIPELINE DE ETL FINALIZADO =====")

if __name__ == "__main__":
    INPUT_FOLDER = 'desafio1/src/etl-prod/input_files' 
    run_production_etl_pipeline(INPUT_FOLDER)
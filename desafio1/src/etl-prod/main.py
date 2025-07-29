
import os
from connection import get_connection
from load_data import load_silver_to_gold
from validate_data import validate_data

def run_silver_to_gold_pipeline(silver_folder_path):
    """
    Orquestra a execução do pipeline de ETL final, movendo os dados
    da camada Silver (Parquet) para a camada Gold (SQL Server).
    """
    print("===== INICIANDO PIPELINE DE ETL (SILVER -> GOLD) =====")
    
    connection = None
    try:
        connection = get_connection()
        
        if connection:

            load_silver_to_gold(connection, silver_folder_path)
            
            print("\n--- Iniciando Validação Final na Camada Gold ---")
            validate_data(connection)
            
    except Exception as e:
        print(f"Ocorreu um erro fatal no orquestrador principal: {e}")
    finally:
        if connection:
            connection.close()
            print("\nConexão com o banco de dados fechada.")
            
    print("===== PIPELINE DE ETL (SILVER -> GOLD) FINALIZADO =====")

if __name__ == "__main__":
    SILVER_INPUT_FOLDER = "/app/data-lake/silver/res/getGuestChecks" 
    run_silver_to_gold_pipeline(SILVER_INPUT_FOLDER)
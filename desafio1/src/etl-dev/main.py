from connection import get_connection
from clean_database import clean_all_tables
from load_data import load_all_data
from validate_data import validate_data

def run_full_etl_pipeline():

    print("===== INICIANDO PIPELINE DE ETL COMPLETO =====")
    
    connection = None
    try:
        connection = get_connection()
        
        if connection:
            clean_all_tables(connection)
            load_all_data(connection)
            validate_data(connection)
            
    except Exception as e:
        print(f"Ocorreu um erro fatal no orquestrador principal: {e}")
    finally:
        if connection:
            connection.close()
            print("\nConexão com o banco de dados fechada.")
            
    print("===== PIPELINE DE ETL FINALIZADO =====")

if __name__ == "__main__":
    run_full_etl_pipeline()
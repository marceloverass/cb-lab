import pandas as pd
import json
import os
from glob import glob

BRONZE_PATH = "/app/data-lake/bronze"
SILVER_PATH = "/app/data-lake/silver"


def process_bronze_to_silver(source_endpoint):
    """
    Lê os dados JSON da camada Bronze para um endpoint específico,
    aplica limpezas e transformações, e salva na camada Silver em formato Parquet.
    """
    source_path = os.path.join(BRONZE_PATH, source_endpoint)
    print(f"INFO: Iniciando processamento da camada Bronze para: {source_path}")

    json_files = glob(os.path.join(source_path, "**", "*.json"), recursive=True)

    if not json_files:
        print(f"AVISO: Nenhum arquivo JSON encontrado em {source_path}.")
        return

    for file_path in json_files:
        try:
            print(f"INFO: Processando arquivo: {file_path}")
            
            with open(file_path, 'r') as f:
                raw_data = json.load(f)

            if 'guestChecks' in raw_data and raw_data['guestChecks']:
                
                df_normalized = pd.json_normalize(
                    raw_data, 
                    record_path=['guestChecks'], 
                    sep='_',
                    meta=['locRef']
                )
                
                colunas_rename_map = {
                    'guestCheckId': 'guest_check_id', 'chkNum': 'numero_pedido',
                    'opnBusDt': 'data_negocio_aberto', 'opnUTC': 'data_abertura_utc',
                    'clsdUTC': 'data_fechamento_utc', 'clsdFlag': 'fechado',
                    'gstCnt': 'total_pessoas', 'subTtl': 'sub_total',
                    'chkTtl': 'total_pedido', 'dscTtl': 'total_desconto',
                    'payTtl': 'total_pago', 'tblName': 'numero_mesa',
                    'empNum': 'numero_funcionario'
                    
                }
    
                df_silver = df_normalized.copy()
                df_silver.rename(columns=colunas_rename_map, inplace=True)
                
                if 'data_abertura_utc' in df_silver.columns:
                    df_silver['data_abertura_utc'] = pd.to_datetime(df_silver['data_abertura_utc'], errors='coerce')
                if 'data_fechamento_utc' in df_silver.columns:
                    df_silver['data_fechamento_utc'] = pd.to_datetime(df_silver['data_fechamento_utc'], errors='coerce')
                if 'fechado' in df_silver.columns:
                    df_silver['fechado'] = df_silver['fechado'].astype(bool)

                relative_path = os.path.relpath(os.path.dirname(file_path), BRONZE_PATH)
                silver_dir_path = os.path.join(SILVER_PATH, relative_path)
                os.makedirs(silver_dir_path, exist_ok=True)
                
                base_filename = os.path.basename(file_path).replace('.json', '.parquet')
                silver_file_path = os.path.join(silver_dir_path, base_filename)
                
                df_silver.to_parquet(silver_file_path, index=False)
                print(f"SUCESSO: Dados transformados e salvos na camada SILVER em: {silver_file_path}")
            
            else:
                print(f"AVISO: Arquivo {file_path} é simulado ou não contém 'guestChecks'. Ignorando.")

        except Exception as e:
            print(f"ERRO: Falha ao processar o arquivo {file_path}. Causa: {e}")

if __name__ == "__main__":
    endpoints_a_processar = [
        'bi/getFiscalInvoice',
        'res/getGuestChecks',
        'org/getChargeBack',
        'trans/getTransactions',
        'inv/getCashManagementDetails'
    ]
    for endpoint in endpoints_a_processar:
        process_bronze_to_silver(endpoint)
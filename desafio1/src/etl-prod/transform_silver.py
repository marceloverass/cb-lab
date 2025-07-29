import pandas as pd
import json
import os
from glob import glob
from datetime import datetime

PROJECT_ROOT = "/app"
BRONZE_PATH = os.path.join(PROJECT_ROOT, "data-lake", "bronze")
SILVER_PATH = os.path.join(PROJECT_ROOT, "data-lake", "silver")

def process_bronze_to_silver(source_endpoint):
    """
    Lê os dados JSON da camada Bronze, aplica limpezas e transformações de forma
    inteligente, e salva na camada Silver em formato Parquet.
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
            
                df_normalized = pd.json_normalize(raw_data, record_path=['guestChecks'], sep='_')

                colunas_relevantes = [
                    'guestCheckId', 'chkNum', 'opnBusDt', 'opnUTC', 'clsdUTC', 'clsdFlag',
                    'gstCnt', 'subTtl', 'chkTtl', 'dscTtl', 'payTtl', 'tblName', 'empNum'
                ]
                colunas_existentes = [col for col in colunas_relevantes if col in df_normalized.columns]
                df_silver = df_normalized[colunas_existentes]

                # Renomear colunas
                df_silver = df_silver.rename(columns={
                    'guestCheckId': 'guest_check_id', 'chkNum': 'numero_pedido',
                    'opnBusDt': 'data_negocio_aberto', 'opnUTC': 'data_abertura_utc',
                    'clsdUTC': 'data_fechamento_utc', 'clsdFlag': 'fechado',
                    'gstCnt': 'total_pessoas', 'subTtl': 'sub_total',
                    'chkTtl': 'total_pedido', 'dscTtl': 'total_desconto',
                    'payTtl': 'total_pago', 'tblName': 'numero_mesa',
                    'empNum': 'numero_funcionario'
                })

                if 'data_abertura_utc' in df_silver.columns:
                    df_silver['data_abertura_utc'] = pd.to_datetime(df_silver['data_abertura_utc'])
                if 'data_fechamento_utc' in df_silver.columns:
                    df_silver['data_fechamento_utc'] = pd.to_datetime(df_silver['data_fechamento_utc'])
                if 'fechado' in df_silver.columns:
                    df_silver['fechado'] = df_silver['fechado'].astype(bool)

                relative_path = os.path.relpath(os.path.dirname(file_path), source_path)
                silver_dir_path = os.path.join(SILVER_PATH, source_endpoint, relative_path)
                os.makedirs(silver_dir_path, exist_ok=True)
                
                base_filename = os.path.basename(file_path).replace('.json', '.parquet')
                silver_file_path = os.path.join(silver_dir_path, base_filename)
                
                df_silver.to_parquet(silver_file_path, index=False)
                print(f"SUCESSO: Dados transformados e salvos na camada SILVER em: {silver_file_path}")
            
            else:
                print(f"AVISO: Arquivo {file_path} é um arquivo simulado ou não contém dados válidos. Ignorando.")

        except Exception as e:
            print(f"ERRO: Falha ao processar o arquivo {file_path}. Causa: {e}")

if __name__ == "__main__":
    process_bronze_to_silver('res/getGuestChecks')
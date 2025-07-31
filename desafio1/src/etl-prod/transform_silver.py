import pandas as pd
import json
import os
from glob import glob

BRONZE_PATH = "/app/data-lake/bronze"
SILVER_PATH = "/app/data-lake/silver"

def process_bronze_to_silver(source_endpoint):
    """
    Lê os dados JSON da camada Bronze, aplica transformações específicas
    para cada endpoint e salva na camada Silver em formato Parquet.
    """
    source_path = os.path.join(BRONZE_PATH, source_endpoint)
    print(f"INFO: Iniciando processamento para o endpoint: {source_endpoint}")

    json_files = glob(os.path.join(source_path, "**", "*.json"), recursive=True)

    if not json_files:
        print(f"AVISO: Nenhum arquivo JSON encontrado em {source_path}.")
        return

    for file_path in json_files:
        try:
            print(f"INFO: Processando arquivo: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            if source_endpoint in ['res/getGuestChecks', 'org/getChargeBack']:
                
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
        
                    colunas_existentes = {k: v for k, v in colunas_rename_map.items() if k in df_normalized.columns}
                    df_silver = df_normalized.rename(columns=colunas_existentes)
                    
                    if 'data_abertura_utc' in df_silver.columns:
                        df_silver['data_abertura_utc'] = pd.to_datetime(df_silver['data_abertura_utc'], errors='coerce')
                    if 'data_fechamento_utc' in df_silver.columns:
                        df_silver['data_fechamento_utc'] = pd.to_datetime(df_silver['data_fechamento_utc'], errors='coerce')
                    if 'fechado' in df_silver.columns:
                        df_silver['fechado'] = df_silver['fechado'].astype(bool)

                    save_to_silver(df_silver, file_path, BRONZE_PATH, SILVER_PATH)
                else:
                    print(f"AVISO: Arquivo {file_path} do tipo '{source_endpoint}' não continha dados em 'guestChecks'. Ignorando.")
            
            elif source_endpoint == 'bi/getFiscalInvoice':
                print(f"INFO: Lógica para '{source_endpoint}' ainda não implementada. Ignorando arquivo.")
                # TODO: Implementar a normalização e transformação para notas fiscais aqui.
                pass
            
            else:
                print(f"AVISO: Nenhuma lógica de transformação definida para o endpoint '{source_endpoint}'. Ignorando arquivo: {file_path}")

        except Exception as e:
            print(f"ERRO: Falha crítica ao processar o arquivo {file_path}. Causa: {e}")

def save_to_silver(df, original_file_path, bronze_base, silver_base):
    """
    Função auxiliar para salvar um DataFrame na camada Silver, mantendo a estrutura de pastas.
    """
    relative_path = os.path.relpath(os.path.dirname(original_file_path), bronze_base)
    silver_dir_path = os.path.join(silver_base, relative_path)
    os.makedirs(silver_dir_path, exist_ok=True)
    
    base_filename = os.path.basename(original_file_path).replace('.json', '.parquet')
    silver_file_path = os.path.join(silver_dir_path, base_filename)
    
    df.to_parquet(silver_file_path, index=False)
    print(f"SUCESSO: Dados salvos na camada SILVER em: {silver_file_path}")

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
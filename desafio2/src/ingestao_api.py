import json
import os
from datetime import datetime
from glob import glob

# --- 1. Configuração ---
BASE_URL = "https://api.restaurant-chain.com"
ENDPOINTS = [
    "/bi/getFiscalInvoice",
    "/res/getGuestChecks",
    "/org/getChargeBack",
    "/trans/getTransactions",
    "/inv/getCashManagementDetails"
]
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
INPUT_FILES_PATH = os.path.join(PROJECT_ROOT, "desafio1", "src", "etl-prod", "input_files")

# --- 2. Função para descobrir os parâmetros dinamicamente ---
def discover_parameters(input_folder_path):
    print(f"INFO: Lendo arquivos de '{input_folder_path}' para descobrir parâmetros de ingestão...")
    payloads = []
    json_files = glob(os.path.join(input_folder_path, "*.json"))
    if not json_files:
        print(f"AVISO: Nenhum arquivo JSON de entrada encontrado em '{input_folder_path}'.")
        return [], {}

    store_id_to_file_map = {}
    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                store_id = data.get('locRef')
                business_date = data.get('guestChecks', [{}])[0].get('opnBusDt')
                if store_id and business_date:
                    payload = {"storeId": store_id, "busDt": business_date}
                    if payload not in payloads:
                        payloads.append(payload)
                        store_id_to_file_map[store_id] = file_path # Mapeia o ID ao caminho do arquivo
                else:
                    print(f"AVISO: Não foi possível extrair 'locRef' ou 'opnBusDt' do arquivo {file_path}")
        except Exception as e:
            print(f"ERRO: Falha ao ler o arquivo {file_path}. Causa: {e}")
            
    print(f"INFO: {len(payloads)} conjunto(s) de parâmetros descobertos.")
    return payloads, store_id_to_file_map

# --- 3. Função de Chamada da API (Simulação Dinâmica) ---
def call_api(endpoint, payload, file_map):
    """
    Simula uma chamada POST lendo o arquivo JSON correspondente ao storeId.
    """
    print(f"INFO: Chamando endpoint: {endpoint} com payload: {payload}")
    store_id = payload['storeId']
    
    # Se o endpoint for getGuestChecks, usamos o arquivo real correspondente
    if "getGuestChecks" in endpoint and store_id in file_map:
        try:
            source_file = file_map[store_id]
            print(f"DEBUG: Simulando resposta com o arquivo: {source_file}")
            with open(source_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"ERRO: Falha ao ler o arquivo de simulação {source_file}. Causa: {e}")
            return {"status": "error", "message": "Failed to read simulation file"}
    else:
        # Para todos os outros endpoints, retorna um JSON genérico
        return {"endpoint": endpoint, "storeId": store_id, "status": "success", "data": [], "payload_used": payload}

# --- 4. Lógica de Armazenamento no Data Lake (Camada Bronze) ---
def save_to_bronze_layer(endpoint_name, store_id, business_date_str, data):
    try:
        business_date = datetime.strptime(business_date_str, "%Y-%m-%d")
        year, month, day = business_date.year, f"{business_date.month:02d}", f"{business_date.day:02d}"
        dir_path = os.path.join(PROJECT_ROOT, "data-lake", "bronze", endpoint_name.strip("/"), f"year={year}", f"month={month}", f"day={day}")
        os.makedirs(dir_path, exist_ok=True)
        file_name = f"storeId={store_id.replace(' ', '')}_data.json"
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"SUCESSO: Dados salvos na camada BRONZE em: {file_path}")
    except Exception as e:
        print(f"ERRO: Falha ao salvar na camada Bronze. Causa: {e}")

# --- 5. Orquestração ---
def run_ingestion_pipeline():
    print("--- Iniciando Pipeline de Ingestão para a Camada BRONZE ---")
    
    payloads_to_process, file_map = discover_parameters(INPUT_FILES_PATH)
    
    if not payloads_to_process:
        print("Nenhum parâmetro válido encontrado. Pipeline encerrado.")
        return

    for payload in payloads_to_process:
        for endpoint in ENDPOINTS:
            response_data = call_api(endpoint, payload, file_map)
            if response_data:
                save_to_bronze_layer(endpoint, payload["storeId"], payload["busDt"], response_data)
    
    print("--- Pipeline de Ingestão para a Camada BRONZE Finalizado ---")

if __name__ == "__main__":
    run_ingestion_pipeline()
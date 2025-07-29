import pandas as pd
import os
from glob import glob
import numpy as np

def _delete_existing_order(cursor, guest_check_id):
    """Função auxiliar para apagar um pedido existente e todos os seus detalhes."""
    print(f"INFO: Pedido {guest_check_id} já existe. Removendo versão antiga...")
    cursor.execute("DELETE FROM Detalhe_ItemMenu WHERE item_menu_detalhe_id IN (SELECT id_detalhe_especifico FROM Linhas_Detalhe WHERE guest_check_id_fk = ? AND tipo_detalhe = 'MENU_ITEM')", guest_check_id)
    cursor.execute("DELETE FROM Linhas_Detalhe WHERE guest_check_id_fk = ?", guest_check_id)
    cursor.execute("DELETE FROM Impostos_Pedidos WHERE guest_check_id_fk = ?", guest_check_id)
    cursor.execute("DELETE FROM Pedidos WHERE guest_check_id = ?", guest_check_id)
    print(f"INFO: Versão antiga do pedido {guest_check_id} removida.")

def load_silver_to_gold(cnxn, silver_folder_path):
    if not cnxn:
        print("ERRO: Carga de dados não pode ser executada: conexão inválida.")
        return

    cursor = cnxn.cursor()
    
    try:
        # --- ETAPA 1: EXTRAÇÃO DA CAMADA SILVER ---
        print(f"\nINFO: Iniciando extração da Camada Silver do caminho: {silver_folder_path}")
        parquet_files = glob(os.path.join(silver_folder_path, "**", "*.parquet"), recursive=True)

        if not parquet_files:
            print(f"AVISO: Nenhum arquivo Parquet encontrado em {silver_folder_path}.")
            return

        df_silver = pd.concat([pd.read_parquet(f, engine='pyarrow') for f in parquet_files])
        print(f"SUCESSO: {len(df_silver)} registros de pedidos lidos da camada Silver.")
        
        # --- ETAPA 2: SINCRONIZAÇÃO DOS CATÁLOGOS ---
        print("INFO: Sincronizando tabelas de catálogo...")
        if 'locRef' in df_silver.columns:
            for loc_ref in df_silver['locRef'].unique():
                cursor.execute("IF NOT EXISTS (SELECT 1 FROM Restaurantes WHERE loc_ref = ?) INSERT INTO Restaurantes (loc_ref) VALUES (?);", str(loc_ref), str(loc_ref))
        
        for emp_num_numpy in df_silver['numero_funcionario'].unique():
            emp_num = int(emp_num_numpy)
            cursor.execute("IF NOT EXISTS (SELECT 1 FROM Funcionarios WHERE numero_funcionario = ?) INSERT INTO Funcionarios (numero_funcionario, nome_completo, cargo) VALUES (?, ?, ?);",
                           emp_num, emp_num, f'Funcionario {emp_num}', 'Garçom')
        
        cursor.execute("IF NOT EXISTS (SELECT 1 FROM Formas_Pagamento_Catalogo WHERE nome = 'Cartão de Crédito') BEGIN INSERT INTO Formas_Pagamento_Catalogo (nome) VALUES ('Cartão de Crédito') END;")
        cursor.execute("IF NOT EXISTS (SELECT 1 FROM Erros_Catalogo WHERE codigo_erro = 101) BEGIN INSERT INTO Erros_Catalogo (codigo_erro, descricao_curta) VALUES (101, 'Erro de Impressão') END;")
        
        cnxn.commit()
        print("INFO: Catálogos sincronizados.")

        # --- ETAPA 3: CARGA NA CAMADA GOLD (SQL SERVER) ---
        for index, check_row in df_silver.iterrows():
            guest_check_id = int(check_row['guest_check_id'])
            
            try:
                cursor.execute("SELECT COUNT(1) FROM Pedidos WHERE guest_check_id = ?", guest_check_id)
                if cursor.fetchone()[0] > 0:
                    _delete_existing_order(cursor, guest_check_id)
                
                cursor.execute("SELECT restaurante_id FROM Restaurantes WHERE loc_ref = ?", str(check_row['locRef']))
                restaurante_id = cursor.fetchone()[0]
                cursor.execute("SELECT funcionario_id FROM Funcionarios WHERE numero_funcionario = ?", int(check_row['numero_funcionario']))
                funcionario_id = cursor.fetchone()[0]

                sql_pedidos = "INSERT INTO Pedidos (guest_check_id, restaurante_id_fk, funcionario_id_fk, numero_pedido, data_negocio_aberto, data_abertura_utc, data_fechamento_utc, fechado, total_pedido, total_desconto, total_pago, numero_mesa) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
                cursor.execute(sql_pedidos, guest_check_id, restaurante_id, funcionario_id, int(check_row['numero_pedido']), pd.to_datetime(check_row['data_negocio_aberto']).date(), pd.to_datetime(check_row['data_abertura_utc']), pd.to_datetime(check_row['data_fechamento_utc']), bool(check_row['fechado']), float(check_row['total_pedido']), float(check_row['total_desconto']), float(check_row['total_pago']), str(check_row['numero_mesa']))
                
                taxes_list = check_row.get('taxes')
                if taxes_list is not None and isinstance(taxes_list, np.ndarray):
                    taxes_list = taxes_list.tolist()
                
                if taxes_list:
                    for tax in taxes_list:
                        sql_impostos = "INSERT INTO Impostos_Pedidos (guest_check_id_fk, numero_imposto, total_venda_tributavel, total_imposto_cobrado, taxa_imposto) VALUES (?, ?, ?, ?, ?);"
                        cursor.execute(sql_impostos, guest_check_id, tax['taxNum'], tax['txblSlsTtl'], tax['taxCollTtl'], tax['taxRate'])
                
                detailLines_list = check_row.get('detailLines')
                if detailLines_list is not None and isinstance(detailLines_list, np.ndarray):
                    detailLines_list = detailLines_list.tolist()

                if detailLines_list:
                    for line in detailLines_list:
                        tipo_detalhe, id_detalhe_especifico = (None, None)
                        if 'menuItem' in line and line['menuItem']:
                            tipo_detalhe = 'MENU_ITEM'
                            mi = line['menuItem']
                            sql_item_menu = "INSERT INTO Detalhe_ItemMenu (numero_item_menu, modificado, imposto_incluso, impostos_ativos, nivel_preco) VALUES (?, ?, ?, ?, ?);"
                            cursor.execute(sql_item_menu, mi['miNum'], mi['modFlag'], mi['inclTax'], mi['activeTaxes'], mi['prcLvl'])
                            cursor.execute("SELECT SCOPE_IDENTITY();")
                            id_detalhe_especifico = cursor.fetchone()[0]

                        if tipo_detalhe and id_detalhe_especifico is not None:
                            sql_linhas_detalhe = "INSERT INTO Linhas_Detalhe (guest_check_line_item_id, guest_check_id_fk, numero_linha, data_detalhe_utc, total_liquido, quantidade, tipo_detalhe, id_detalhe_especifico) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
                            cursor.execute(sql_linhas_detalhe, line['guestCheckLineItemId'], guest_check_id, line['lineNum'], line['detailUTC'], line['dspTtl'], line['dspQty'], tipo_detalhe, id_detalhe_especifico)
                
                cnxn.commit()
                print(f"SUCESSO: Pedido {guest_check_id} carregado para a camada Gold com todos os detalhes.")

            except Exception as e_inner:
                print(f"ERRO ao processar o pedido {guest_check_id} para a camada Gold: {e_inner}")
                cnxn.rollback()
    except Exception as e_outer:
        print(f"ERRO CRÍTICO durante o processo Silver-to-Gold: {e_outer}")
    finally:
        cursor.close()
import json
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

def load_all_data(connection):
    if not connection:
        print("Carga de dados não pode ser executada: objeto de conexão inválido.")
        return

    print("\nIniciando processo de carga de dados...")
    cursor = connection.cursor()
    
    try:
        json_path = os.path.join(PROJECT_ROOT, 'desafio1', 'data', 'ERP.json')
        print(f"Lendo arquivo de dados de: {json_path}")

        with open(json_path, 'r') as f:
            data = json.load(f)

        # --- Transform & Load (Tabelas de Catálogo e Dimensão) ---
        print("Populando tabelas de catálogo e obtendo IDs de forma explícita...")

        # --- Restaurantes ---
        restaurante_ref = data['locRef']
        cursor.execute("SELECT restaurante_id FROM Restaurantes WHERE loc_ref = ?", restaurante_ref)
        row = cursor.fetchone()
        if row:
            restaurante_id = row[0]
            print(f"Restaurante '{restaurante_ref}' já existe com ID: {restaurante_id}")
        else:
            cursor.execute("INSERT INTO Restaurantes (loc_ref) VALUES (?);", restaurante_ref)
            connection.commit()
            cursor.execute("SELECT restaurante_id FROM Restaurantes WHERE loc_ref = ?", restaurante_ref)
            restaurante_id = cursor.fetchone()[0]
            print(f"Restaurante '{restaurante_ref}' inserido com ID: {restaurante_id}")

        # --- Funcionarios ---
        emp_num = data['guestChecks'][0]['empNum']
        cursor.execute("SELECT funcionario_id FROM Funcionarios WHERE numero_funcionario = ?", emp_num)
        row = cursor.fetchone()
        if row:
            funcionario_id = row[0]
            print(f"Funcionário '{emp_num}' já existe com ID: {funcionario_id}")
        else:
            cursor.execute("INSERT INTO Funcionarios (numero_funcionario, nome_completo, cargo) VALUES (?, ?, ?);", 
                           emp_num, f'Funcionario {emp_num}', 'Garçom')
            connection.commit()
            cursor.execute("SELECT funcionario_id FROM Funcionarios WHERE numero_funcionario = ?", emp_num)
            funcionario_id = cursor.fetchone()[0]
            print(f"Funcionário '{emp_num}' inserido com ID: {funcionario_id}")
        
        cursor.execute("IF NOT EXISTS (SELECT 1 FROM Formas_Pagamento_Catalogo WHERE nome = 'Cartão de Crédito') INSERT INTO Formas_Pagamento_Catalogo (nome) VALUES ('Cartão de Crédito');")
        cursor.execute("IF NOT EXISTS (SELECT 1 FROM Erros_Catalogo WHERE codigo_erro = 101) INSERT INTO Erros_Catalogo (codigo_erro, descricao_curta) VALUES (101, 'Erro de Impressão');")
        print("Tabelas de catálogo populadas.")
        
        # --- Transform & Load (Tabelas de Transação) ---
        for check in data.get('guestChecks', []):
            sql_pedidos = """
            INSERT INTO Pedidos (guest_check_id, restaurante_id_fk, funcionario_id_fk, numero_pedido, data_negocio_aberto, 
                                 data_abertura_utc, data_fechamento_utc, fechado, total_pedido, total_desconto, 
                                 total_pago, numero_mesa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            cursor.execute(sql_pedidos, 
                           check['guestCheckId'], restaurante_id, funcionario_id, check['chkNum'], check['opnBusDt'],
                           check['opnUTC'], check['clsdUTC'], check['clsdFlag'], check['chkTtl'],
                           check['dscTtl'], check['payTtl'], check['tblName'])
            
            for tax in check.get('taxes', []):
                sql_impostos = """
                INSERT INTO Impostos_Pedidos (guest_check_id_fk, numero_imposto, total_venda_tributavel,
                                              total_imposto_cobrado, taxa_imposto)
                VALUES (?, ?, ?, ?, ?);
                """
                cursor.execute(sql_impostos,
                               check['guestCheckId'], tax['taxNum'], tax['txblSlsTtl'],
                               tax['taxCollTtl'], tax['taxRate'])

        print("Tabelas de transação populadas.")
        connection.commit()

        # --- Lógica Polimórfica ---
        print("\nProcessando a lógica polimórfica...")
        for check in data.get('guestChecks', []):
            guest_check_id = check['guestCheckId']
            
            for line in check.get('detailLines', []):
                tipo_detalhe = None
                id_detalhe_especifico = None

                if 'menuItem' in line:
                    tipo_detalhe = 'MENU_ITEM'
                    mi = line['menuItem']
                    sql_item_menu = """
                    INSERT INTO Detalhe_ItemMenu (numero_item_menu, modificado, imposto_incluso, 
                                                  impostos_ativos, nivel_preco)
                    VALUES (?, ?, ?, ?, ?);
                    """
                    cursor.execute(sql_item_menu, mi['miNum'], mi['modFlag'], mi['inclTax'], 
                                   mi['activeTaxes'], mi['prcLvl'])
                    
                    cursor.execute("SELECT SCOPE_IDENTITY();")
                    id_detalhe_especifico = cursor.fetchone()[0]

                if tipo_detalhe and id_detalhe_especifico is not None:
                    sql_linhas_detalhe = """
                    INSERT INTO Linhas_Detalhe (guest_check_line_item_id, guest_check_id_fk, numero_linha, 
                                                data_detalhe_utc, total_liquido, quantidade, 
                                                tipo_detalhe, id_detalhe_especifico)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """
                    cursor.execute(sql_linhas_detalhe,
                                   line['guestCheckLineItemId'], guest_check_id, line['lineNum'],
                                   line['detailUTC'], line['dspTtl'], line['dspQty'],
                                   tipo_detalhe, id_detalhe_especifico)

        connection.commit()
        print("Carga de dados concluída com sucesso.")
        
    except Exception as e:
        print(f"Ocorreu um erro durante a carga de dados: {e}")
        connection.rollback()
    finally:
        cursor.close()
import json

def _delete_existing_order(cursor, guest_check_id):
    """Função otimizada de exclusão com controle transacional"""
    print(f"INFO: Atualizando pedido {guest_check_id}...")
    
    # Deletar registros relacionados em ordem hierárquica
    cursor.execute("""
        DELETE FROM Detalhe_ItemMenu 
        WHERE item_menu_detalhe_id IN (
            SELECT ld.id_detalhe_especifico 
            FROM Linhas_Detalhe ld 
            WHERE ld.guest_check_id_fk = ? AND ld.tipo_detalhe = 'MENU_ITEM'
        )
    """, guest_check_id)
    
    # Deletar outros tipos de detalhe (preparado para expansão futura)
    cursor.execute("""
        DELETE FROM Detalhe_Desconto 
        WHERE desconto_detalhe_id IN (
            SELECT ld.id_detalhe_especifico 
            FROM Linhas_Detalhe ld 
            WHERE ld.guest_check_id_fk = ? AND ld.tipo_detalhe = 'DISCOUNT'
        )
    """, guest_check_id)
    
    cursor.execute("""
        DELETE FROM Detalhe_TaxaServico 
        WHERE taxa_servico_detalhe_id IN (
            SELECT ld.id_detalhe_especifico 
            FROM Linhas_Detalhe ld 
            WHERE ld.guest_check_id_fk = ? AND ld.tipo_detalhe = 'SERVICE_CHARGE'
        )
    """, guest_check_id)
    
    cursor.execute("""
        DELETE FROM Detalhe_FormaPagamento 
        WHERE pagamento_detalhe_id IN (
            SELECT ld.id_detalhe_especifico 
            FROM Linhas_Detalhe ld 
            WHERE ld.guest_check_id_fk = ? AND ld.tipo_detalhe = 'PAYMENT'
        )
    """, guest_check_id)
    
    cursor.execute("""
        DELETE FROM Detalhe_Erro 
        WHERE erro_detalhe_id IN (
            SELECT ld.id_detalhe_especifico 
            FROM Linhas_Detalhe ld 
            WHERE ld.guest_check_id_fk = ? AND ld.tipo_detalhe = 'ERROR'
        )
    """, guest_check_id)
    
    # Deletar tabelas pai
    cursor.execute("DELETE FROM Linhas_Detalhe WHERE guest_check_id_fk = ?", guest_check_id)
    cursor.execute("DELETE FROM Impostos_Pedidos WHERE guest_check_id_fk = ?", guest_check_id)
    cursor.execute("DELETE FROM Pedidos WHERE guest_check_id = ?", guest_check_id)

def load_all_data(connection, json_file_path):
    if not connection:
        print("ERRO: Carga de dados não pode ser executada: objeto de conexão inválido.")
        return
    
    # CRÍTICO: Desabilitar auto-commit
    connection.autocommit = False
    cursor = connection.cursor()
    
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)

        # Garantir que restaurante e funcionário existem
        restaurante_ref = data['locRef']
        cursor.execute("SELECT restaurante_id FROM Restaurantes WHERE loc_ref = ?", restaurante_ref)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Restaurantes (loc_ref) VALUES (?);", restaurante_ref)
        
        emp_num = data['guestChecks'][0]['empNum']
        cursor.execute("SELECT funcionario_id FROM Funcionarios WHERE numero_funcionario = ?", emp_num)
        if not cursor.fetchone():
            cursor.execute("INSERT INTO Funcionarios (numero_funcionario, nome_completo, cargo) VALUES (?, ?, ?);", 
                           emp_num, f'Funcionario {emp_num}', 'Garçom')
        
        # Commit das entidades base (separado)
        connection.commit()
        
        # Processar cada pedido em transação individual
        for check in data.get('guestChecks', []):
            guest_check_id = check['guestCheckId']
            
            # INICIAR NOVA TRANSAÇÃO PARA CADA PEDIDO
            try:
                # Verificar se pedido já existe
                cursor.execute("SELECT COUNT(1) FROM Pedidos WHERE guest_check_id = ?", guest_check_id)
                if cursor.fetchone()[0] > 0:
                    _delete_existing_order(cursor, guest_check_id)
                
                # Buscar IDs de referência
                cursor.execute("SELECT restaurante_id FROM Restaurantes WHERE loc_ref = ?", data['locRef'])
                restaurante_id = cursor.fetchone()[0]
                cursor.execute("SELECT funcionario_id FROM Funcionarios WHERE numero_funcionario = ?", check['empNum'])
                funcionario_id = cursor.fetchone()[0]

                # Inserir novo pedido
                sql_pedidos = """INSERT INTO Pedidos (guest_check_id, restaurante_id_fk, funcionario_id_fk, 
                                numero_pedido, data_negocio_aberto, data_abertura_utc, data_fechamento_utc, 
                                fechado, total_pedido, total_desconto, total_pago, numero_mesa) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
                cursor.execute(sql_pedidos, (
                    check['guestCheckId'], restaurante_id, funcionario_id, check['chkNum'], 
                    check['opnBusDt'], check['opnUTC'], check['clsdUTC'], check['clsdFlag'], 
                    check['chkTtl'], check['dscTtl'], check['payTtl'], check['tblName']
                ))
                
                # Inserir impostos do pedido
                for tax in check.get('taxes', []):
                    sql_impostos = """INSERT INTO Impostos_Pedidos (guest_check_id_fk, numero_imposto, 
                                     total_venda_tributavel, total_imposto_cobrado, taxa_imposto) 
                                     VALUES (?, ?, ?, ?, ?);"""
                    cursor.execute(sql_impostos, (
                        check['guestCheckId'], tax['taxNum'], tax['txblSlsTtl'], 
                        tax['taxCollTtl'], tax['taxRate']
                    ))
                
                # COLETAR TODOS OS DADOS DE INSERÇÃO ANTES DE INSERIR
                # Isso evita inserções parciais que podem falhar
                detalhes_para_inserir = []
                
                for line in check.get('detailLines', []):
                    if 'menuItem' in line:
                        mi = line['menuItem']
                        detalhe_data = {
                            'line_data': line,
                            'menu_item_data': (mi['miNum'], mi['modFlag'], mi['inclTax'], mi['activeTaxes'], mi['prcLvl']),
                            'tipo_detalhe': 'MENU_ITEM'
                        }
                        detalhes_para_inserir.append(detalhe_data)
                
                # INSERIR TODOS OS DETALHES EM LOTE
                for detalhe in detalhes_para_inserir:
                    # Inserir detalhe específico
                    if detalhe['tipo_detalhe'] == 'MENU_ITEM':
                        sql_item_menu = """INSERT INTO Detalhe_ItemMenu (numero_item_menu, modificado, 
                                          imposto_incluso, impostos_ativos, nivel_preco) OUTPUT INSERTED.item_menu_detalhe_id
                                          VALUES (?, ?, ?, ?, ?);"""
                        cursor.execute(sql_item_menu, detalhe['menu_item_data'])
                        result = cursor.fetchone()
                        
                        if result is None:
                            raise Exception("Falha ao obter ID do item de menu inserido")
                        
                        id_detalhe_especifico = result[0]
                        
                        # Validar se o ID é válido
                        if id_detalhe_especifico is None:
                            raise Exception("ID do detalhe específico é NULL")
                        
                        # Inserir linha de detalhe imediatamente após
                        line = detalhe['line_data']
                        sql_linhas_detalhe = """INSERT INTO Linhas_Detalhe (guest_check_line_item_id, 
                                               guest_check_id_fk, numero_linha, data_detalhe_utc, 
                                               total_liquido, quantidade, tipo_detalhe, id_detalhe_especifico) 
                                               VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""
                        cursor.execute(sql_linhas_detalhe, (
                            line['guestCheckLineItemId'], guest_check_id, line['lineNum'], 
                            line['detailUTC'], line['dspTtl'], line['dspQty'], 
                            detalhe['tipo_detalhe'], id_detalhe_especifico
                        ))
                
                # Se chegou até aqui, commit da transação completa
                connection.commit()
                print(f"SUCESSO: Pedido {guest_check_id} processado e salvo.")
                
            except Exception as e_inner:
                print(f"ERRO ao processar o pedido {guest_check_id}: {e_inner}")
                connection.rollback()
                print(f"ROLLBACK executado para pedido {guest_check_id}")
                # Não re-levantar a exceção, continuar com outros pedidos
                
    except Exception as e_outer:
        print(f"ERRO CRÍTICO durante a carga de dados: {e_outer}")
        connection.rollback()
        
    finally:
        cursor.close()
        # Restaurar auto-commit se necessário
        connection.autocommit = True

# Função para limpeza manual de registros órfãos
def cleanup_orphaned_records(connection):
    """Remove registros órfãos do banco de dados"""
    cursor = connection.cursor()
    try:
        # Encontrar registros órfãos
        cursor.execute("""
            SELECT COUNT(*) FROM Detalhe_ItemMenu 
            WHERE item_menu_detalhe_id NOT IN (
                SELECT DISTINCT id_detalhe_especifico 
                FROM Linhas_Detalhe 
                WHERE tipo_detalhe = 'MENU_ITEM' 
                AND id_detalhe_especifico IS NOT NULL
            )
        """)
        orphans_count = cursor.fetchone()[0]
        print(f"Registros órfãos encontrados: {orphans_count}")
        
        if orphans_count > 0:
            cursor.execute("""
                DELETE FROM Detalhe_ItemMenu 
                WHERE item_menu_detalhe_id NOT IN (
                    SELECT DISTINCT id_detalhe_especifico 
                    FROM Linhas_Detalhe 
                    WHERE tipo_detalhe = 'MENU_ITEM' 
                    AND id_detalhe_especifico IS NOT NULL
                )
            """)
            connection.commit()
            print(f"Limpeza concluída: {orphans_count} registros órfãos removidos.")
        
    except Exception as e:
        print(f"Erro durante limpeza: {e}")
        connection.rollback()
    finally:
        cursor.close()
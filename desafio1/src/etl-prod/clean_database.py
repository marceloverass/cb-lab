def clean_all_tables(connection):
    if not connection:
        print("Limpeza não pode ser executada: objeto de conexão inválido.")
        return

    print("Iniciando limpeza das tabelas...")
    cursor = connection.cursor()
    
    try:
        cursor.execute("DELETE FROM Detalhe_Erro;")
        cursor.execute("DELETE FROM Detalhe_FormaPagamento;")
        cursor.execute("DELETE FROM Detalhe_TaxaServico;")
        cursor.execute("DELETE FROM Detalhe_Desconto;")
        cursor.execute("DELETE FROM Detalhe_ItemMenu;")
        cursor.execute("DELETE FROM Linhas_Detalhe;")
        cursor.execute("DELETE FROM Impostos_Pedidos;")
        cursor.execute("DELETE FROM Pedidos;")
        cursor.execute("DELETE FROM Erros_Catalogo;")
        cursor.execute("DELETE FROM Formas_Pagamento_Catalogo;")
        cursor.execute("DELETE FROM Funcionarios;")
        cursor.execute("DELETE FROM Restaurantes;")
        
        print("Resetando contadores de identidade...")
        cursor.execute("DBCC CHECKIDENT ('Restaurantes', RESEED, 0);")
        cursor.execute("DBCC CHECKIDENT ('Funcionarios', RESEED, 0);")
        cursor.execute("DBCC CHECKIDENT ('Formas_Pagamento_Catalogo', RESEED, 0);")
        cursor.execute("DBCC CHECKIDENT ('Erros_Catalogo', RESEED, 0);")
        cursor.execute("DBCC CHECKIDENT ('Impostos_Pedidos', RESEED, 0);")
        cursor.execute("DBCC CHECKIDENT ('Detalhe_ItemMenu', RESEED, 0);")
        cursor.execute("DBCC CHECKIDENT ('Detalhe_Desconto', RESEED, 0);")
        cursor.execute("DBCC CHECKIDENT ('Detalhe_TaxaServico', RESEED, 0);")
        cursor.execute("DBCC CHECKIDENT ('Detalhe_FormaPagamento', RESEED, 0);")
        cursor.execute("DBCC CHECKIDENT ('Detalhe_Erro', RESEED, 0);")
        
        connection.commit()
        print("Tabelas limpas e contadores de identidade resetados com sucesso.")

    except Exception as e:
        print(f"Erro durante a limpeza das tabelas: {e}")
        print("Desfazendo transação (rollback)...")
        connection.rollback()
    finally:
        cursor.close()
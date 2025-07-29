def validate_data(connection):
    if not connection:
        print("Validação não pode ser executada: objeto de conexão inválido.")
        return

    print("\n--- Iniciando Validação dos Dados ---")
    cursor = connection.cursor()
    
    try:
        tabelas = [
            "Restaurantes", "Funcionarios", "Formas_Pagamento_Catalogo", "Erros_Catalogo",
            "Pedidos", "Impostos_Pedidos", "Linhas_Detalhe", "Detalhe_ItemMenu",
            "Detalhe_Desconto", "Detalhe_TaxaServico", "Detalhe_FormaPagamento", "Detalhe_Erro"
        ]
        
        print("Contagem de registros por tabela:")
        for tabela in tabelas:
            # Executa uma contagem de linhas para cada tabela
            cursor.execute(f"SELECT COUNT(*) FROM {tabela};")
            count = cursor.fetchone()[0]
            print(f"- {tabela}: {count} registro(s)")

    except Exception as e:
        print(f"Ocorreu um erro durante a validação dos dados: {e}")
    finally:
        cursor.close()
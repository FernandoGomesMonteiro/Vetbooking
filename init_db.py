import mysql.connector

def init_db():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='usuario',
        database='vetbooking'
    )
    cursor = conn.cursor()
    
    # Verifica se a tabela principal já existe
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'vetbooking' 
        AND table_name = 'usuarios'
    """)
    tabela_existe = cursor.fetchone()[0] > 0
    
    # Se a tabela não existir, executa o script
    if not tabela_existe:
        with open('bdVetBooking.sql', encoding='utf-8') as f:
            script = f.read()
            commands = script.split(';')
            for cmd in commands:
                if cmd.strip():
                    cursor.execute(cmd)
        conn.commit()
        print("Banco de dados inicializado com sucesso!")
    else:
        print("Banco já está inicializado. Nenhuma ação necessária.")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    init_db()
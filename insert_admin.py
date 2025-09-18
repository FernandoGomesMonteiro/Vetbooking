import mysql.connector
from werkzeug.security import generate_password_hash
import datetime

def insert_admin_user():
    print('Inserindo usuário administrador no banco de dados...')
    
    try:
        # Conectar ao banco de dados vetbooking
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='usuario',
            database='vetbooking'
        )
        cursor = conn.cursor()
        
        # Verificar se o email do admin já existe na tabela de médicos
        admin_email = 'admin@vetbooking.com'
        cursor.execute('SELECT * FROM medicos WHERE email = %s', (admin_email,))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print(f"O usuário administrador com email {admin_email} já existe.")
        else:
            # Dados do administrador
            nome_admin = 'Administrador'
            senha_admin = generate_password_hash('admin123')
            crmv = 'ADMIN'
            uf = 'SP'
            especialidades = 'Administração'
            descricao = 'Usuário administrador do sistema'
            data_cadastro = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Inserir o administrador na tabela de médicos
            cursor.execute(
                'INSERT INTO medicos (nome_medico, email, senha, crmv, uf, especialidades, descricao, data_cadastro) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                (nome_admin, admin_email, senha_admin, crmv, uf, especialidades, descricao, data_cadastro)
            )
            
            # Commit das alterações
            conn.commit()
            print(f"Usuário administrador criado com sucesso!")
            print(f"Email: {admin_email}")
            print(f"Senha: admin123")
        
        # Fechar cursor e conexão
        cursor.close()
        conn.close()
        
        return True
    
    except mysql.connector.Error as err:
        print(f"Erro ao inserir usuário administrador: {err}")
        return False

if __name__ == '__main__':
    print("=== Inserção de Usuário Administrador no VetBooking ===")
    insert_admin_user()
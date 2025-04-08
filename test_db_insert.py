import sqlite3
import os
from werkzeug.security import generate_password_hash

def test_database_insert():
    print('Testando inserção no banco de dados...')
    
    try:
        # Verificar se o banco de dados existe
        if not os.path.exists('database.db'):
            print('Erro: O arquivo database.db não existe!')
            return False
        
        # Conectar ao banco de dados
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Inserir um tutor de teste
        try:
            # Verificar se o tutor de teste já existe
            cursor.execute('SELECT * FROM tutores WHERE email = ?', ('teste@example.com',))
            existing_tutor = cursor.fetchone()
            
            if not existing_tutor:
                cursor.execute(
                    'INSERT INTO tutores (nome, email, senha, endereco, cep, data_nascimento) VALUES (?, ?, ?, ?, ?, ?)',
                    ('Usuário Teste', 'teste@example.com', generate_password_hash('senha123'), 'Rua Teste, 123', '80000-000', '1990-01-01')
                )
                conn.commit()
                print('Tutor de teste inserido com sucesso!')
            else:
                print('Tutor de teste já existe no banco de dados.')
            
            # Verificar se a inserção foi bem-sucedida
            cursor.execute('SELECT * FROM tutores WHERE email = ?', ('teste@example.com',))
            tutor = cursor.fetchone()
            if tutor:
                print(f'Tutor encontrado: ID={tutor[0]}, Nome={tutor[1]}, Email={tutor[2]}')
            else:
                print('Erro: Tutor não encontrado após inserção!')
        
        except Exception as e:
            print(f'Erro ao inserir tutor: {e}')
            conn.rollback()
        
        # Fechar conexão
        conn.close()
        print('Teste de inserção concluído!')
        return True
    
    except Exception as e:
        print(f'Erro ao testar inserção no banco de dados: {e}')
        return False

if __name__ == '__main__':
    test_database_insert()